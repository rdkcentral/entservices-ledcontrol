To execute the cases inside qemu

cd /tmp

git clone git@github.com:rdkcentral/entservices-ledcontrol.git

cd entservices-ledcontrol/Tests/vDeviceTests

Execute the suiteManager without profiling:
python3 SuiteManager.py

Execute the suiteManager with profiling enabled:
python3 SuiteManager.py -time 

Plugin Activation will be done in the initial stage while running the SuiteManager

Plugin activation is now done by default before suite execution:
- org.rdk.LEDControl -> Controller.1.activate(callsign=org.rdk.LEDControl)

Disable default activation only if needed:
- export AUTO_ACTIVATE_PLUGINS=0


If all LED indicator cases fail with "connection refused", configure endpoint host/ports before running.

Defaults used by the tests:
- MW JSON-RPC: http://127.0.0.1:9998/jsonrpc
- vComponent API: http://127.0.0.1:8080/api/postKVP

Useful overrides:
- TARGET_HOST (applies to both endpoints)
- JSONRPC_PORT
- VCOMPONENT_PORT
- WPEFRAMEWORK_JSONRPC_URL (full URL, highest priority)
- VCOMPONENT_API_URL (full URL, highest priority)

Examples:

# when running directly inside QEMU guest (services on localhost) without profiling
python3 SuiteManager.py

# when running directly inside QEMU guest (services on localhost) with profiling
python3 SuiteManager.py -time

# when running from host against QEMU target IP without profiling
export TARGET_HOST=192.168.1.50
export JSONRPC_PORT=9998
export VCOMPONENT_PORT=8080
python3 SuiteManager.py

# when running from host against QEMU target IP with profiling
export TARGET_HOST=192.168.1.50
export JSONRPC_PORT=9998
export VCOMPONENT_PORT=8080
python3 SuiteManager.py -time

# full URL override form without profiling
export WPEFRAMEWORK_JSONRPC_URL=http://192.168.1.50:9998/jsonrpc
export VCOMPONENT_API_URL=http://192.168.1.50:8080/api/postKVP
python3 SuiteManager.py

# full URL override form with profiling
export WPEFRAMEWORK_JSONRPC_URL=http://192.168.1.50:9998/jsonrpc
export VCOMPONENT_API_URL=http://192.168.1.50:8080/api/postKVP
python3 SuiteManager.py -time


errors incase if any:-

hdmicec_post_command.sh not found - 
here in the testcases add the path where hdmicec_post_command.sh script is present inside the qemu 
for eg tmp/vDeviceTests/vHdmiCec/vComponent_configurations/hdmicec_post_command.sh