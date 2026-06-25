"""
/**
 * @file TCID14_Full_Device_Lifecycle.py
 * @brief L2 LED indicator functional testcase.
 *
 * @testcase TCID14_Full_Device_Lifecycle
 * @details TCID14_test_l2_led_full_device_lifecycle validates the 'full device lifecycle' LED behavior using JSON-RPC and/or vComponent state simulation.
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
    Start_Profiling = time.perf_counter()  # Profiling started - track execution time for full device lifecycle (IP_ACQUIRED -> WPS_CONNECTING -> WPS_CONNECTED -> ACTIVE -> STANDBY -> DEEP_SLEEP)
    log_info("TCID14_test_l2_led_full_device_lifecycle - Scenario: Full Device Lifecycle")
    log_info("  BOOT->ACTIVE(IP_ACQUIRED)->WPS_CONNECTING->WPS_CONNECTED->STANDBY->DEEP_SLEEP(STANDBY)")

    # (yaml_file, expected_mw_state, description)
    # BOOT is AIDL-only, not in MW enum -> getLEDState will return NONE (unrecognised)
    # IP_ACQUIRED -> ACTIVE, DEEP_SLEEP -> STANDBY per aidlStateToLEDControlState
    steps = [
        ("SetState_IP_ACQUIRED.yaml",   "ACTIVE",        "IP acquired (network up)"),
        ("SetState_WPS_CONNECTING.yaml","WPS_CONNECTING", "WPS session start"),
        ("SetState_WPS_CONNECTED.yaml", "WPS_CONNECTED",  "WPS paired"),
        ("SetState_ACTIVE.yaml",         "ACTIVE",        "Normal operation"),
        ("SetState_STANDBY.yaml",        "STANDBY",       "User standby"),
        ("SetState_DEEP_SLEEP.yaml",     "STANDBY",       "Deep sleep (maps to STANDBY)"),
    ]

    overall_pass = True
    for yaml_file, expected, description in steps:
        label = yaml_file.replace('SetState_', '').replace('indicator_set_state_', '').replace('.yaml', '')
        log_info(f"\n-- [{description}] set {label} -> expect MW {expected} --")
        if not _post(yaml_file):
            log_error(f"  vComponent POST failed: {yaml_file}")
            overall_pass = False
            continue
        time.sleep(2)
        actual = _get_led_state()
        log_warning(f"  getLEDState -> '{actual}'  (expected '{expected}')")
        if actual != expected:
            log_error(f"  Mismatch: got '{actual}', expected '{expected}'")
            overall_pass = False
        else:
            log_success(f"  OK ✔")

    if overall_pass:
        Elapsed_Profile = time.perf_counter() - Start_Profiling  # Profiling ends - compute total time taken to complete the full device lifecycle flow across all state transitions
        log_success("TCID14_Full_Device_Lifecycle Passed ✅" + f" time consumed: {Elapsed_Profile:.3f}s")
    else:
        log_error("TCID14_Full_Device_Lifecycle Failed ❌")
    return overall_pass
