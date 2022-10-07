from shutil import rmtree, copy2
from urllib import request
from pathlib import Path
from zipfile import ZipFile
import json
from os import environ, remove, fspath
from typing import Generator, Tuple
from subprocess import PIPE, run
import logging

logging.basicConfig(
    format="[%(levelname)s][%(asctime)s] - %(message)s",
    datefmt="%d/%b/%y-%H:%M:%S",
    level=logging.INFO,
)


def download_links(links: str, out: str) -> Generator[dict, None, None]:
    """
    Given a file with a list of urls per ecah line,
    it will download the files into the given output folder.
    It returns one dictionary per link with the following keys:
        url: str = The link you passed in the list of links
        result: bool = Whether it was downloaded
        msg: str = Additional info on the success/failure
        out: str|None = Path to the downloaded file
    """
    for url in Path(links).read_text().split("\n"):
        try:
            if url == "":
                continue
            if not Path(out).exists():
                raise FileNotFoundError("The output folder does not exist.")
            target = f"{out}/tmp/{url.split('/')[-1]}"
            Path(target).parent.mkdir(exist_ok=True, parents=True)
            _, msg = request.urlretrieve(url, target)
            yield {"url": url, "result": True, "msg": "OK", "out": target}
        except Exception as e:
            yield {"url": url, "result": False, "msg": e, "out": None}


def extract_zip(
    zip_file: str, img_formats: Tuple[str]
) -> Generator[Path, None, None]:
    """
    Extracts a zip file in a given directory and yields the extracted files
    as Path objects. It checks whether there is at least one FBX file and
    one image file inside of the zip package. If any of both items are missing,
    the process is aborted.
    """
    with ZipFile(zip_file, "r") as ftr:
        if all(".fbx" not in f.filename for f in ftr.filelist):
            raise Exception("Missing FBX file, process aborted for this url")

        # Note: if there are no images in the zip, the process could be aborted
        # at his point, however a FBX may be reexported even though it doesn't
        # need to be processed. This is the reason why the following two lines
        # are commented. In case the execution should be aborted if no images
        # are found in the zip, the following two lines will handle it.

        # if all(tag not in f.filename for tag in img_formats for f in ftr.filelist):
        #     raise Exception("Missing image files, process aborted for this url")

        for file in ftr.filelist:
            yield Path(ftr.extract(file, Path(zip_file).parent))


if "__main__" == __name__:

    import argparse
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "list", type=str, help="Text file that contains one download link per line."
    )
    parser.add_argument(
        "out", type=str, help="Folder where the downloaded files should be stored"
    )
    args = parser.parse_args()
    download_results = list(download_links(args.list, args.out))

    with open(environ.get("CONFIG"), "r") as ftr:
        config = json.load(ftr)

    for item in download_results:
        logging.info("-" * 30)
        logging.info(f"Working on url {item.get('url')}")
        if not item.get("result"):
            logging.warning(item.get("msg"))
            continue

        try:
            extracted_files = list(
                extract_zip(
                    item.get("out"), config.get("SUPPORTED_IMAGE_FORMATS")
                )
            )
        except Exception as e:

            logging.warning(e)
            continue

        fbx_file = [f for f in extracted_files if f.suffix == ".fbx"][0]
        image_files = [
            f
            for f in extracted_files
            if f.suffix in config.get("SUPPORTED_IMAGE_FORMATS")
        ]

        if image_files == list():
            exported_fbx = Path(args.out, fbx_file.stem, fbx_file.name)
            exported_fbx.parent.mkdir(exist_ok=True, parents=True)
            copy2(fbx_file, fspath(exported_fbx))
            logging.warning(f"The zip {item.get('out')} contained no valid "
                "image files, and thus it won't be processed, but just "
                "copied to the export directory instead.")
            continue

        p = run(
            [
                environ.get("MAYAPY22_BIN"),
                environ.get("MAYA_BATCH_MODULE"),
                fbx_file,
                args.out,
                *image_files,
            ],
            stdout=PIPE,
            stderr=PIPE,
            env=environ,
        )
        logging.debug(f"Printing maya output:")
        for line in p.stdout.decode("utf-8").split("\n"):
            logging.debug(f"[MAYA OUTPUT] - {line}")
        for line in p.stderr.decode("utf-8").split("\n"):
            logging.warning(line)
        logging.debug(f"[MAYA OUTPUT] - {line}")

    # Removing downloaded files and tmp files
    try:
        rmtree(Path(args.out, "tmp"))
    except:
        logging.warning(f"Failed to remove temporal dir {args.out}/tmp")

