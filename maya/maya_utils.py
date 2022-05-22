"""
This module contains Maya utility functions and can only be ran from within a
Maya environment. These functions can be used independently and are stateless.

Note: # type: ignore is used here so that there is no PyLance linting error for
missing imports (Maya libraries is not accesible by the IDE)
"""

from pathlib import Path
from typing import List, Generator, Tuple
from os import environ, fspath
from re import findall
from shutil import copy2

try:
    # Note: # type: ignore is used here so that there is no PyLance linting
    # error for missing imports (Maya libraries is not accesible by the IDE)
    import maya.cmds as cmds  # type: ignore
    import maya.mel as mm  # type: ignore
    from maya.api.OpenMaya import MGlobal  # type: ignore

    printError = MGlobal.displayError
    printWarning = MGlobal.displayWarning

except:
    raise ImportError(
        "This module depends on Autodesk's Maya internal libraries, "
        "please load it from within a Maya environment."
    )

NOT_ALPHNUM = r"[^A-Za-z0-1]"  # Any character that is not alphanumeric


def return_materials() -> Generator[str, None, None]:
    """
    Yields the materials that are assigned to meshes in the current maya scene.
    It will ignore any material that has no connections to the file's meshes.
    """
    for mesh in cmds.ls(type="mesh"):
        for shader in cmds.listConnections(mesh, type="shadingEngine"):
            if cmds.sets(shader, q=True):
                for mat in cmds.ls(cmds.listConnections(shader), materials=True):
                    yield mat


def return_all_meshes() -> Generator[str, None, None]:
    """
    Yields all the meshes and meshes transform nodes in the scene.
    """
    for mesh in cmds.ls(type="mesh"):
        transform = cmds.listRelatives(mesh, p=True)[0]
        yield mesh
        yield transform


def freeze_all_meshes_transforms(nodes: List[str]) -> None:
    """
    Freezes all the passed transfroms `nodes`.
    """
    for node in return_all_meshes():
        if cmds.objectType(node) == "transform":
            cmds.makeIdentity(node, apply=True, t=True, r=True, s=True, pn=True)


def export_fbx(
    output: str, export_preset: str = None, export_selected: bool = True
) -> None:
    """
    Exports the current Maya scene as an FBX `output`.
    If a `export_preset` file is not passed, it will used the defaults
    set in the scene. It also checks whether the fbxmaya plugin is loaded and
    it loads if it is not loaded.
    """
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    if export_preset is not None:
        mm.eval(f'FBXLoadExportPresetFile -f "{export_preset}"')

    cmds.select(clear=True)
    cmds.select(list(return_all_meshes()))

    return cmds.file(
        output,
        force=True,
        options="v=0;",
        type="FBX export",
        pr=True,
        es=export_selected,
        ea=not export_selected,
    )


def process_fbx_file(
    fbx: Path,
    imgs: List[Path],
    plug_tag_mapping: dict,
    export_folder: str,
    img_formats: Tuple[str] = (".jpg", ".png"),
    export_preset: str = None,
) -> None:
    """
    Given a FBX `fbx` file and a `imgs` list of images which extensions can
    be found in the tuple `img_formats`, this method exports a
    new FBX file with the passed export preset `export_preset` after attempting
    to assign the textures to the fbx materials based on a series of rules:
    1.- The texture must contain both the name of the FBX file and material
    within its name, regardless of the arrangement of these.
    2.- The texture must contain a tag -or identifier- within its name
    which must be found in the dictionary `plug_tag_mapping` as a key.
    The value to this key is the material slot where the image must be inserted.
    If the slot is found in the material, the image will be assigned.

    Parameters:
        fbx (Path): fbx file to import and export
        imgs (List[Path]): list of textures that should be attached to the materials
            within the fbx file.
        plug_tag_mapping (dict): flat dictionary containing a tag-plug pair.
            i.e.: {"BC" : "color", "R" : "roughness}
        img_formats (Tuple[str]): tuple containing accepted image files.
        export_preset (str): path to the fbx export preset

    Returns:
    None
    """

    # Prepping the maya file
    cmds.file(new=True, f=True)
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    cmds.file(fbx, i=True, type="FBX", ignoreVersion=True, options="fbx")
    freeze_all_meshes_transforms(list(return_all_meshes()))
    scene_materials = list(return_materials())

    for img in imgs:

        # Filter out invalid input.
        if img.suffix not in img_formats:
            printError(
                f"The file {img.name} doesn't have any of the supported formats: "
                f"{img_formats}"
            )
            continue
        if fbx.stem not in fspath(img.stem):
            printError(
                f"Mismatch between FBX name and image name: {fbx.name}, {img.name}"
            )
            continue

        # Looking for one of the supported map type tags
        plug: str = None
        for tag in plug_tag_mapping:
            result_plug = findall(
                r"(^|{1}){0}({1}|$)".format(tag, NOT_ALPHNUM), img.stem
            )
            # The regex above finds a tag that is not surrounded by alphanumeric
            # values, so that it allows for flexible naming convention.
            # I.E.: BC_example_whatever.jpg, example_BC.jpg, BC.example.jpg

            if result_plug == list():
                continue
            else:
                plug = plug_tag_mapping[tag]
                break

        if plug is None:
            printError(
                f"Failed to find a suitable plug for the texture {img.name}. "
                f"Valid plug tags are: {list(plug_tag_mapping)}"
            )
            continue

        # Matching texture and material.
        for mat in scene_materials:
            if mat not in img.stem:
                printError(
                    "Missmatch betweeen the materials in the FBX: "
                    f"{scene_materials} and the texture {img.stem}"
                )
                continue

            if plug in cmds.listAttr(mat):

                # Making use of MEL macro for creating + connecting textures
                texture_node = mm.eval(
                    'createRenderNodeCB -as2DTexture "" file '
                    '"defaultNavigation -force true -connectToExisting '
                    f'-source %node -destination {mat}.{plug};";'
                )
                img_path = Path(export_folder, fbx.stem, "images")
                img_path.mkdir(exist_ok=True, parents=True)
                exported_img = Path(img_path, img.name)
                copy2(img, exported_img)
                cmds.setAttr(
                    f"{texture_node}.fileTextureName",
                    fspath(exported_img),
                    type="string",
                )
            else:
                printError(f"Failed to find the {plug} connection in material {mat}")

    export_folder = Path(export_folder, fbx.stem)
    # export_folder.mkdir(exist_ok=True)
    printWarning("Export was successful " + fspath(Path(export_folder, fbx.name)))
    export_fbx(fspath(Path(export_folder, fbx.name)), export_preset)


if "__main__" == __name__:
    import json
    from dotenv import load_dotenv

    load_dotenv()

    with open(environ.get("CONFIG"), "r") as ftr:
        config = json.load(ftr)

    dw_folder = Path("/home/rasputin/repositories/cgtrader/_task/test/export/tmp/58de157c")
    process_fbx_file(
        [f for f in dw_folder.glob("*") if f.suffix == ".fbx"][0],
        [f for f in dw_folder.glob("*") if f.suffix in (".jpg", ".png")],
        config.get("PLUG_TAG2NAME"),
        "/home/rasputin/repositories/cgtrader/_task/test/export",
        config.get("SUPPORTED_IMAGE_FORMATS"),
        environ.get("FBX_EXPORT_PRESET"),

    )
