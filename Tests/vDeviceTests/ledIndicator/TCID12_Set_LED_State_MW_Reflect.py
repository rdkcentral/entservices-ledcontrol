"""
/**
 * @file TCID12_Set_Led_State_Mw_Reflect.py
 * @brief L2 LED indicator functional testcase.
 *
 * @testcase TCID12_Set_LED_State_MW_Reflect
 * @details TCID12_test_l2_led_set_led_state_mw_reflect validates the 'set led state mw reflect' LED behavior using JSON-RPC and/or vComponent state simulation.
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


def _get_led_state():
    resp = send_curl_command(ledIndicator_Curl.get_led_state)
    if not resp or resp == "< No response from WPEFramework >":
        return None
    try:
        return json.loads(resp).get("result", {}).get("state")
    except json.JSONDecodeError:
        return None


def run_test():
    Start_Profiling = time.perf_counter()  # Profiling started - track execution time for MW setLEDState and getLEDState round-trip verification across all supported states
    log_info("TCID12_test_l2_led_set_led_state_mw_reflect - Scenario: setLEDState via MW API for each supported state")
    log_info("  Calls MW setLEDState then immediately reads back with getLEDState")

    # (curl_cmd_attr, expected_state)
    steps = [
        (ledIndicator_Curl.set_led_state_active,        "ACTIVE"),
        (ledIndicator_Curl.set_led_state_standby,       "STANDBY"),
        (ledIndicator_Curl.set_led_state_wps_connecting, "WPS_CONNECTING"),
        (ledIndicator_Curl.set_led_state_wps_connected,  "WPS_CONNECTED"),
        (ledIndicator_Curl.set_led_state_wps_error,      "WPS_ERROR"),
        (ledIndicator_Curl.set_led_state_factory_reset,  "FACTORY_RESET"),
        (ledIndicator_Curl.set_led_state_usb_upgrade,    "USB_UPGRADE"),
        (ledIndicator_Curl.set_led_state_download_error, "DOWNLOAD_ERROR"),
    ]

    overall_pass = True
    for set_cmd, expected in steps:
        log_info(f"\n-- setLEDState to {expected} --")
        set_resp = send_curl_command(set_cmd)
        log_warning(f"  setLEDState response: {set_resp}")
        if not set_resp or set_resp == "< No response from WPEFramework >":
            log_error(f"  No response for setLEDState({expected})")
            overall_pass = False
            continue
        try:
            set_json = json.loads(set_resp)
            result = set_json.get("result")
            set_ok = (result is True) or (
                isinstance(result, dict) and result.get("success", False)
            )
            if not set_ok:
                log_error(f"  setLEDState({expected}) returned success=false")
                overall_pass = False
                continue
        except json.JSONDecodeError:
            log_error(f"  Invalid JSON for setLEDState({expected})")
            overall_pass = False
            continue

        time.sleep(1)
        actual = _get_led_state()
        log_warning(f"  getLEDState -> '{actual}'  (expected '{expected}')")
        if actual != expected:
            log_error(f"  Mismatch: got '{actual}', expected '{expected}'")
            overall_pass = False
        else:
            log_success(f"  OK: {actual} ✔")

    if overall_pass:
        Elapsed_Profile = time.perf_counter() - Start_Profiling  # Profiling ends - compute total time taken for all setLEDState/getLEDState round-trip verifications
        log_success("TCID12_Set_LED_State_MW_Reflect Passed ✅" + f" time consumed: {Elapsed_Profile:.3f}s")
    else:
        log_error("TCID12_Set_LED_State_MW_Reflect Failed ❌")
    return overall_pass
