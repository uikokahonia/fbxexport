
### Running this tool
The **./test** folder contains two scripts that can be run in order to test this tool:
  * **./test/run_http_server.sh**: starts an http server in localhost:8000 on the **./test** folder
  * **./run_test.sh**: runs the **./main.py** with the required arguments:
    * a txt file with link downloads
    * an export folder
  * These scripts expect to have a a python3 virtual environment running that has python-dotenv installed.

### Additional notes
* Please note that even though there is a **./test** folder, this tool is not unit-tested.
* The **.env** file must be set up for each computer.
* The **./maya** folder contains files related to the maya environment, and can be reused in other applications.
* The maya scripts were written for Maya2022, which has a python3.7 interpreter by default. This tool won't work with previous versions of Maya, although translating these scripts into python2.7 wouldn't be much work. 
* All pyhton libraries are builtin except for python-dotenv, which must be installed.
* The CLI format was chosen so that in can be easily sent to a farm, however implementing it as a GUI would be very easy and fast
* The naming convention of the images can be arranged in any way as long as it contains:
  * The name of the FBX file
  * The name of the material it belongs to
  * A tag that represents a map type (BC, R, N, O etc.) which must be specified in the config.json file.
  * I.E.:
    * 'T_{fbxfilename}_{materialname}_O'
    * '{fbxfilename}\_O\_{materialname}_O'
    * '{resolution}\_O\_{fbxfilename}\_{prjname}\_{materialname}'