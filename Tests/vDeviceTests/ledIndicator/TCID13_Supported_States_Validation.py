"""
/**
 * @file TCID13_Supported_States_Validation.py
 * @brief L2 LED indicator functional testcase.
 *
 * @testcase TCID13_Supported_States_Validation
 * @details TCID13_test_l2_led_supported_states_validation validates the 'supported states validation' LED behavior using JSON-RPC and/or vComponent state simulation.
 *
 * @precondition
 *  - org.rdk.LEDControl plugin is active and JSON-RPC endpoint is reachable.
 *  - Indicator vComponent command path is available for emulation-driven checks.
 *
 * @dependencies
 *  - utils.py
 *  - ledIndicator_Curl.py
 *  - suiteManager.py
 *  - vcomponent_configurations/indicator/commands/*.yaml (for vComponent scenarios)
 *
 * @expected_result
 *  - API/state transition results match expected values for the testcase flow.
 *
 * @pass_criteria
 *  - Validation checks pass and testcase returns True.
 *
 * @failure_criteria
 *  - Response mismatch, command failure, JSON parsing error, or testcase returns False.
 */
"""

import time
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import (
    send_curl_command,
    log_info,
    log_success,
    log_error,
    log_warning
)
import ledIndicator_Curl


# These are the MW-level state names that should be returned.
# BOOT, DEEP_SLEEP, IP_ACQUIRED, OFF, NO_IP, WIFI_ERROR, WPS_SES_OVERLAP, PSU_FAILURE
# are AIDL-only states not mapped to MW enum, so they are excluded.
EXPECTED_STATES = {
    "ACTIVE",
    "STANDBY",
    "WPS_CONNECTING",
    "WPS_CONNECTED",
    "WPS_ERROR",
    "FACTORY_RESET",
    "USB_UPGRADE",
    "DOWNLOAD_ERROR",
}


def run_test():
    Start_Profiling = time.perf_counter()  # Profiling started - track execution time for getSupportedLEDStates content validation against the expected platform state list
    log_info("TCID13_test_l2_led_supported_states_validation - Scenario: getSupportedLEDStates content validation")

    resp = send_curl_command(ledIndicator_Curl.get_supported_led_states)
    if not resp or resp == "< No response from WPEFramework >":
        log_error("  No response from WPEFramework")
        log_error("TCID13_Supported_States_Validation Failed ❌")
        return False

    log_warning(f"  getSupportedLEDStates response: {resp}")

    try:
        resp_json = json.loads(resp)
    except json.JSONDecodeError:
        log_error("  Invalid JSON response")
        log_error("TCID13_Supported_States_Validation Failed ❌")
        return False

    result = resp_json.get("result", {})
    if not result.get("success", False):
        log_error("  success field is false")
        log_error("TCID13_Supported_States_Validation Failed ❌")
        return False

    returned_states = set(result.get("supportedLEDStates", []))
    log_info(f"  Returned states: {sorted(returned_states)}")

    missing = EXPECTED_STATES - returned_states
    if missing:
        log_error(f"  Missing expected states: {missing}")
        log_error("TCID13_Supported_States_Validation Failed ❌")
        return False

    log_success("  All expected states present in getSupportedLEDStates ✔")
    Elapsed_Profile = time.perf_counter() - Start_Profiling  # Profiling ends - compute total time taken to validate all expected states are present in getSupportedLEDStates response
    log_success("TCID13_Supported_States_Validation Passed ✅" + f" time consumed: {Elapsed_Profile:.3f}s")
    return True
