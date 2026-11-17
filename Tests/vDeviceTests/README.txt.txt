To execute the cases inside qemu

cd /tmp

git clone git@github.com:rdkcentral/entservices-ledcontrol.git

cd entservices-ledcontrol/Tests/vDeviceTests

Execute the SuiteManager with time:
python3 SuiteManager.py -t ledindicator

Execute the SuiteManager without time:
python3 SuiteManager.py ledindicator

Run one test:
python3 SuiteManager.py ledindicator --test TCID01_Get_LED_State

Run multiple selected tests by repeating --test.

Plugin activation is done once before suite execution and deactivation is
attempted after the suite finishes, including setup or test failures:
- ledindicator -> Controller.1.activate(callsign=org.rdk.LEDControl)

Disable default activation only if needed:
- export AUTO_ACTIVATE_PLUGINS=0

Plugin activation is retried for up to 40 seconds. The post-activation wait
defaults to 6 seconds and can be changed with:
- export LEDCONTROL_PLUGIN_INIT_WAIT=<seconds>
- export PLUGIN_INIT_WAIT=<seconds> (shared fallback)

Indicator middleware fallback defaults to enabled for compatibility, but an
existing environment value is preserved. It can also be controlled explicitly:
- python3 SuiteManager.py ledindicator --enable-mw-fallback
- python3 SuiteManager.py ledindicator --disable-mw-fallback
- export ENABLE_INDICATOR_MW_FALLBACK=0

The manager logs the effective lifecycle, activation, wait, profiling, fallback,
and selected-test settings at startup.

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

# when running directly inside QEMU guest (services on localhost)
python3 SuiteManager.py ledindicator

# when running from host against QEMU target IP
export TARGET_HOST=192.168.1.50
export JSONRPC_PORT=9998
export VCOMPONENT_PORT=8080
python3 SuiteManager.py ledindicator

# full URL override form
export WPEFRAMEWORK_JSONRPC_URL=http://192.168.1.50:9998/jsonrpc
export VCOMPONENT_API_URL=http://192.168.1.50:8080/api/postKVP
python3 SuiteManager.py ledindicator


errors incase if any:-

hdmicec_post_command.sh not found - 
here in the testcases add the path where hdmicec_post_command.sh script is present inside the qemu 
for eg tmp/vDeviceTests/vHdmiCec/vComponent_configurations/hdmicec_post_command.sh