"""
/**
 * @file ledIndicator_Curl.py
 * @brief LED Control JSON-RPC API definitions and curl command builders.
 *
 * @testcase ledIndicator_Curl
 * @details Provides pre-built curl commands for LED Control JSON-RPC API calls including getLEDState, getSupportedLEDStates, and setLEDState with state-specific builders.
 *
 * @precondition
 *  - JSON-RPC endpoint is configured and accessible via environment variables or defaults.
 *
 * @dependencies
 *  - json (Python standard library)
 *  - os (Python standard library)
 *
 * @expected_result
 *  - All API command strings are properly formatted for curl execution.
 *
 * @pass_criteria
 *  - API functions return valid JSON-RPC curl commands.
 *
 * @failure_criteria
 *  - Malformed JSON or invalid endpoint configuration.
 */
"""

import json
import os


_TARGET_HOST = os.environ.get("TARGET_HOST", "127.0.0.1")
_JSONRPC_PORT = os.environ.get("JSONRPC_PORT", "9998")
JSONRPC_URL = (
    os.environ.get("WPEFRAMEWORK_JSONRPC_URL")
    or os.environ.get("JSONRPC_URL")
    or f"http://{_TARGET_HOST}:{_JSONRPC_PORT}/jsonrpc"
)


def _build_jsonrpc_curl(method, request_id, params=None):
    payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        payload["params"] = params
    return (
        'curl --max-time 5 '
        '--header "Content-Type: application/json" '
        '--request POST '
        f"--data-binary '{json.dumps(payload)}' "
        f"{JSONRPC_URL}"
    )


get_led_state = (
    _build_jsonrpc_curl("org.rdk.LEDControl.getLEDState", 0)
)

get_supported_led_states = (
    _build_jsonrpc_curl("org.rdk.LEDControl.getSupportedLEDStates", 1)
)

set_led_state = (
    _build_jsonrpc_curl(
        "org.rdk.LEDControl.setLEDState",
        2,
        params={"state": "FACTORY_RESET"},
    )
)


def make_set_led_state(state_name):
    '''Return a curl command string to set the LED state to the given state name.
    Valid state_name values: ACTIVE, STANDBY, WPS_CONNECTING, WPS_CONNECTED,
    WPS_ERROR, FACTORY_RESET, USB_UPGRADE, DOWNLOAD_ERROR
    '''
    return _build_jsonrpc_curl(
        "org.rdk.LEDControl.setLEDState",
        2,
        params={"state": state_name},
    )


# Convenience pre-built commands for each mappable state
set_led_state_active        = make_set_led_state("ACTIVE")
set_led_state_standby       = make_set_led_state("STANDBY")
set_led_state_wps_connecting = make_set_led_state("WPS_CONNECTING")
set_led_state_wps_connected  = make_set_led_state("WPS_CONNECTED")
set_led_state_wps_error      = make_set_led_state("WPS_ERROR")
set_led_state_factory_reset  = make_set_led_state("FACTORY_RESET")
set_led_state_usb_upgrade    = make_set_led_state("USB_UPGRADE")
set_led_state_download_error = make_set_led_state("DOWNLOAD_ERROR")
