"""
This module instanciates Maya as an standalone (no GUI) process and runs the
process_fbx_file export method.
This module must be passed to Maya's python interpreter from the command line,
along with the following arguments:
    fbx file to import
    *image files to connect to the material
I.E.:
    mayapy path/to/my/fbx.fbx my/texture.jpg my/other/texture.png
"""

from sys import argv
from pathlib import Path
import sys
from os import environ

# Note: # type: ignore is used here so that there is no PyLance linting
# error for missing imports (Maya libraries is not accesible by the IDE)
import maya.standalone as alone # type: ignore
import maya.mel as mm # type: ignore
import json
sys.path.append(environ.get("FBX_EXPORT_LIBRARY"))
from maya_utils import process_fbx_file

if "__main__" == __name__:
    try:
        if len(argv) > 4:
            alone.initialize()

            # Load MEL macro for connecting texture node networks inside Maya
            mm.eval(Path(environ.get("CREATE_NODE_MACRO")).read_text())

            with open(environ.get("CONFIG"), "r") as ftr:
                config = json.load(ftr)
            process_fbx_file(
                Path(argv[1]),
                [Path(f) for f in argv[3:]],
                config.get("PLUG_TAG2NAME"),
                argv[2],
                config.get("SUPPORTED_IMAGE_FORMATS"),
                environ.get("FBX_EXPORT_PRESET"),
            )
        else:
            raise Exception("Too few arguments. At least 2 files are required")
    except Exception as e:
        print(e)
