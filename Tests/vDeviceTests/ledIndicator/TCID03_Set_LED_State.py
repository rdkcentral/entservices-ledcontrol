"""
/**
 * @file TCID03_Set_Led_State.py
 * @brief L2 LED indicator functional testcase.
 *
 * @testcase TCID03_Set_LED_State
 * @details TCID03_test_l2_led_set_led_state validates the 'set led state' LED behavior using JSON-RPC and/or vComponent state simulation.
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
    Start_Profiling = time.perf_counter()  # Profiling started - track execution time for setLEDState API call and success validation
    log_info("Executing the curl command get supported let states - Returns the list of LED states that are actually supported by the platform at runtime. Possible values include NONE, ACTIVE, STANDBY, WPS_CONNECTING, WPS_CONNECTED, WPS_ERROR, FACTORY_RESET, USB_UPGRADE and DOWNLOAD_ERROR")

    curl_response = send_curl_command(
        ledIndicator_Curl.set_led_state
    )

    if not curl_response:
        log_error("✖ curl command not sent")
        return False

    log_success("✔ curl command sent")
    log_warning(f"Response: {curl_response}")

    try:
        response_json = json.loads(curl_response)
        result = response_json.get("result")
        if result is True:
            Elapsed_Profile = time.perf_counter() - Start_Profiling  # Profiling ends - compute total time taken to call setLEDState and confirm the API returned success
            log_success("TCID03_Set_LED_State Passed ✅" + f" time consumed: {Elapsed_Profile:.3f}s")
            return True

        log_error(f"Unexpected setLEDState result: {result}")
        log_error("TCID03_Set_LED_State Failed ❌")
        return False
    except json.JSONDecodeError:
        log_error("Invalid JSON response")
        log_error("TCID03_Set_LED_State Failed ❌")
        return False
