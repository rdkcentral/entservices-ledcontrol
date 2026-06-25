"""
/**
 * @file TCID11_Ip_Acquired_Mapping.py
 * @brief L2 LED indicator functional testcase.
 *
 * @testcase TCID11_IP_Acquired_Mapping
 * @details TCID11_test_l2_led_ip_acquired_mapping validates the 'ip acquired mapping' LED behavior using JSON-RPC and/or vComponent state simulation.
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
    Start_Profiling = time.perf_counter()  # Profiling started - track execution time for IP_ACQUIRED to ACTIVE state mapping verification via vComponent and getLEDState
    log_info("TCID11_test_l2_led_ip_acquired_mapping - Scenario: IP_ACQUIRED maps to MW ACTIVE")
    log_info("  Per aidlStateToLEDControlState: IP_ACQUIRED -> LEDSTATE_ACTIVE")

    log_info("\n-- Step: set IP_ACQUIRED via vComponent --")
    if not _post("SetState_IP_ACQUIRED.yaml"):
        log_error("  vComponent POST failed")
        log_error("TCID11_IP_Acquired_Mapping Failed ❌")
        return False
    time.sleep(2)

    actual = _get_led_state()
    log_warning(f"  getLEDState -> '{actual}'  (expected 'ACTIVE')")
    if actual != "ACTIVE":
        log_error(f"  Mismatch: got '{actual}', expected 'ACTIVE'")
        log_error("TCID11_IP_Acquired_Mapping Failed ❌")
        return False

    log_success("  IP_ACQUIRED correctly mapped to ACTIVE ✔")
    Elapsed_Profile = time.perf_counter() - Start_Profiling  # Profiling ends - compute total time taken to verify IP_ACQUIRED maps correctly to ACTIVE via getLEDState
    log_success("TCID11_IP_Acquired_Mapping Passed ✅" + f" time consumed: {Elapsed_Profile:.3f}s")
    return True
