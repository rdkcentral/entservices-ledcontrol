"""
/**
 * @file TCID01_Get_LED_State.py
 * @brief L2 LED indicator functional testcase.
 *
 * @testcase TCID01_Get_LED_State
 * @details TCID01_Get_LED_State validates the 'get LED state' LED behavior using JSON-RPC and/or vComponent state simulation.
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

import json
import time
from utils import (
    send_curl_command,
    log_info,
    log_success,
    log_error,
    log_warning
)
import ledIndicator_Curl


def run_test():
    Start_Profiling = time.perf_counter()  # Profiling started - track execution time for getLEDState API call and state validation
    valid_states = {
        "NONE",
        "ACTIVE",
        "STANDBY",
        "WPS_CONNECTING",
        "WPS_CONNECTED",
        "WPS_ERROR",
        "FACTORY_RESET",
        "USB_UPGRADE",
        "DOWNLOAD_ERROR",
    }


    log_info("Executing the curl command get led states - Retrieves current state of the LED. e.g. {“state”:”WPS_CONNECTING”}")

    curl_response = send_curl_command(
        ledIndicator_Curl.get_led_state
    )

    if not curl_response:
        log_error("✖ curl command not sent")
        return False

    log_success("✔ curl command sent")
    log_warning(f"Response: {curl_response}")

    try:
        response_json = json.loads(curl_response)
        state = response_json.get("result", {}).get("state")
        if isinstance(state, str) and state in valid_states:
            Elapsed_Profile = time.perf_counter() - Start_Profiling  # Profiling ends - compute total time taken to call getLEDState and verify the response state
            log_success("TCID01_Get_LED_State Passed ✅" + f" time consumed: {Elapsed_Profile:.3f}s")
            return True

        log_error(f"Unexpected LED state: {state}")
        log_error("TCID01_Get_LED_State Failed ❌")
        return False
    except json.JSONDecodeError:
        log_error("Invalid JSON response")
        log_error("TCID01_Get_LED_State Failed ❌")
        return False
