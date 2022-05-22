
The .env file must be set up for each computer.
The test folder contains two scripts that can be run in order to test this tool:
  * ./test/run_http_server.sh just starts an http server in localhost:8000 on the ./test folder
  * ./run_test.sh runs the main.py with the required arguments: a txt file with link downloads and en export folder.
  * These scripts expect to have a venv folder containing a python virtual environment.
  * The working directory should be the folder that contains this document.

Please note that even though there is a ./test folder, it is not unittested
The ./maya folder contains files related to the maya environment, and can be reused in other applications.
All pyhton libraries are builtin except for python-dotenv, which must be installed
The CLI format was chosen so that in can be easily sent to a farm, however implementing it as a GUI would be very easy and fast
The naming convention of the images can be arranged in any way as long as it contains:
  * The name of the FBX file
  * The name of the material it belongs to
  * A tag that represents a map type (BC, R, N, O etc.) which must be specified in the config.json file.