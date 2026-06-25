"""
/**
 * @file TCID10_Deep_Sleep_Wake.py
 * @brief L2 LED indicator functional testcase.
 *
 * @testcase TCID10_Deep_Sleep_Wake
 * @details TCID10_test_l2_led_deep_sleep_wake validates the 'deep sleep wake' LED behavior using JSON-RPC and/or vComponent state simulation.
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
    send_vcomponent_command,
    INDICATOR_CMD_BASE,
    log_info,
    log_success,
    log_error,
    log_warning
)
import ledIndicator_Curl


def _post(yaml_file):
    yaml_path = f"{INDICATOR_CMD_BASE}/{yaml_file}"
    log_info(f"  vComponent POST: {yaml_path}")
    http_code, body = send_vcomponent_command(yaml_path)
    log_info(f"  HTTP {http_code}  body: {body}")
    return 200 <= http_code < 300


def _get_led_state():
    resp = send_curl_command(ledIndicator_Curl.get_led_state)
    if not resp or resp == "< No response from WPEFramework >":
        return None
    try:
        return json.loads(resp).get("result", {}).get("state")
    except json.JSONDecodeError:
        return None


def run_test():
    Start_Profiling = time.perf_counter()  # Profiling started - track execution time for deep sleep and wake sequence (ACTIVE -> DEEP_SLEEP maps to STANDBY -> ACTIVE)
    log_info("TCID10_test_l2_led_deep_sleep_wake - Scenario: Deep Sleep and Wake")
    log_info("  AIDL DEEP_SLEEP maps to MW STANDBY per aidlStateToLEDControlState")
    steps = [
        ("SetState_ACTIVE.yaml",     "ACTIVE"),
        # DEEP_SLEEP -> STANDBY mapping (per aidlStateToLEDControlState in implementation)
        ("SetState_DEEP_SLEEP.yaml", "STANDBY"),
        ("SetState_ACTIVE.yaml",     "ACTIVE"),
    ]
    for yaml_file, expected in steps:
        log_info(f"\n-- Step: set indicator={yaml_file.replace('.yaml','')} -> MW expected={expected} --")
        if not _post(yaml_file):
            log_error(f"  vComponent POST failed: {yaml_file}")
            log_error("TCID10_Deep_Sleep_Wake Failed ❌")
            return False
        time.sleep(2)
        actual = _get_led_state()
        log_warning(f"  getLEDState -> '{actual}'  (expected '{expected}')")
        if actual != expected:
            log_error(f"  Mismatch: got '{actual}', expected '{expected}'")
            log_error("TCID10_Deep_Sleep_Wake Failed ❌")
            return False
        log_success(f"  OK: {actual}")
    Elapsed_Profile = time.perf_counter() - Start_Profiling  # Profiling ends - compute total time taken to complete deep sleep and wake flow including AIDL state mapping
    log_success("TCID10_Deep_Sleep_Wake Passed ✅" + f" time consumed: {Elapsed_Profile:.3f}s")
    return True
