"""
/**
 * @file SuiteManager.py
 * @brief Test suite manager for orchestrating LED indicator test cases.
 *
 * @testcase SuiteManager
 * @details Manages test suite configuration, plugin activation, test case loading, and execution with profiling support.
 *
 * @precondition
 *  - org.rdk.LEDControl plugin is available and accessible via JSON-RPC endpoint.
 *  - Test case modules are present in the ledIndicator directory.
 *
 * @dependencies
 *  - utils.py (for logging and plugin activation utilities)
 *  - Individual test case modules (TCID*.py)
 *
 * @expected_result
 *  - All test cases load and execute successfully with pass/fail status reporting.
 *
 * @pass_criteria
 *  - Test suite completes without exceptions and provides detailed pass/fail summary.
 *
 * @failure_criteria
 *  - Plugin activation failure, module import errors, or test execution exceptions.
 */
"""

import importlib
import io
import sys
import time
from pathlib import Path
import os

from utils import (
    PROFILING_ENABLED_ENV,
    log_error,
    log_info,
    log_success,
    activate_plugin,
    WPEFRAMEWORK_JSONRPC_URL,
)


BASE_DIR = Path(__file__).resolve().parent
SUITES = {
    "ledindicator": {
        "banner": "******************** L2 SUITE - RDK - LED INDICATOR ****************************",
        "module_dir": BASE_DIR / "ledIndicator",
        "tests": [
            "TCID01_Get_LED_State",
            "TCID02_Get_Supported_LED_States",
            "TCID03_Set_LED_State",
            "TCID04_Vcomponent_State_Sequence",
            "TCID05_WPS_Lifecycle",
            "TCID06_WPS_Error_Recovery",
            "TCID07_USB_Upgrade_Lifecycle",
            "TCID08_Factory_Reset_Sequence",
            "TCID09_Download_Error_Recovery",
            "TCID10_Deep_Sleep_Wake",
            "TCID11_IP_Acquired_Mapping",
            "TCID12_Set_LED_State_MW_Reflect",
            "TCID13_Supported_States_Validation",
            "TCID14_Full_Device_Lifecycle",
        ],
    },
}

SUITE_PLUGIN_CALLSIGNS = {
    "ledindicator": "org.rdk.LEDControl",
}

def normalize_suite_name(raw_name):
    return raw_name.strip().replace("_", "").replace("-", "").lower()


def load_test_cases(suite_name):
    suite_config = SUITES[suite_name]
    module_dir = str(suite_config["module_dir"])

    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    test_cases = []
    for module_name in suite_config["tests"]:
        module = importlib.import_module(module_name)
        test_cases.append((module_name, module.run_test))

    return suite_config["banner"], test_cases


def run_suite(suite_name, profiling_enabled=False):
    banner, test_cases = load_test_cases(suite_name)
    print(banner)

    # Enable/disable profiling timer to track execution time for each test.
    os.environ[PROFILING_ENABLED_ENV] = "1" if profiling_enabled else "0"

    # Enable MW fallback for vComponent state simulation to ensure test compatibility.
    os.environ["ENABLE_INDICATOR_MW_FALLBACK"] = "1"

    # Initial plugin activation - activate LEDControl plugin via JSON-RPC before test execution begins.
    auto_activate = os.environ.get("AUTO_ACTIVATE_PLUGINS", "1").lower() not in ("0", "false", "no")
    callsign = SUITE_PLUGIN_CALLSIGNS.get(suite_name)
    if auto_activate and callsign:
        log_info(f"Auto-activating plugin '{callsign}' via {WPEFRAMEWORK_JSONRPC_URL}")
        if activate_plugin(callsign):
            log_success(f"Plugin activated: {callsign}")
            log_info("Waiting 6s for plugin to fully initialise...")
            time.sleep(6)
        else:
            log_error(f"Plugin activation failed: {callsign}")
            log_error("Check JSON-RPC endpoint reachability and plugin availability before running tests.")
            return False

    passed = 0
    failed = 0
    failed_cases = []
    original_stdout = sys.stdout

    # Test suite execution loop - runs each test case sequentially and captures results.
    for tc_name, tc_fn in test_cases:
        log_info(f"\n{'='*60}")
        log_info(f"Running: {tc_name}")
        log_info(f"{'='*60}")
        captured = io.StringIO()
        sys.stdout = captured
        try:
            result = tc_fn()
        except Exception as exc:
            result = False
            print(f"EXCEPTION in {tc_name}: {exc}")
        finally:
            sys.stdout = original_stdout

        output = captured.getvalue()
        print(output, end="")

        if result:
            passed += 1
            log_success(f"[PASS] {tc_name}")
        else:
            failed += 1
            failed_cases.append(tc_name)
            log_error(f"[FAIL] {tc_name}")

        time.sleep(1)

    log_info(f"\n{'='*60}")
    log_info(f"Suite Summary: {passed} passed, {failed} failed")
    if failed_cases:
        log_error(f"Failed cases: {failed_cases}")
    log_info(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    args = sys.argv[1:]
    profiling_enabled = False

    if args and args[0] == "-t":
        profiling_enabled = True
        args = args[1:]

    if len(args) < 1:
        print("Usage: python suiteManager.py [-t] <suite_name>")
        print(f"Available suites: {list(SUITES.keys())}")
        sys.exit(1)

    suite_arg = normalize_suite_name(args[0])
    matching = [k for k in SUITES if normalize_suite_name(k) == suite_arg]
    if not matching:
        log_error(f"Unknown suite '{args[0]}'. Available: {list(SUITES.keys())}")
        sys.exit(1)

    ok = run_suite(matching[0], profiling_enabled=profiling_enabled)
    sys.exit(0 if ok else 1)
