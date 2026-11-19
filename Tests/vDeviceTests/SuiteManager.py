"""
/**
 * @file SuiteManager.py
 * @brief Test suite manager for orchestrating LED indicator test cases.
 *
 * @testcase SuiteManager
 * @details Loads selected LED indicator tests, activates and initializes required plugins
 *          for each test, and reports pass/fail/skip results.
 *
 * @precondition
 *  - org.rdk.LEDControl is available through the configured JSON-RPC endpoint.
 *  - Test case modules are present in the ledIndicator directory.
 *
 * @dependencies
 *  - utils.py
 *  - Individual test case modules (TCID*.py)
 *
 * @expected_result
 *  - All selected test cases execute and plugin cleanup completes.
 *
 * @pass_criteria
 *  - Each test returns True (PASSED) or utils.SKIPPED (SKIPPED).
 *
 * @failure_criteria
 *  - Setup, test execution, result validation, or plugin cleanup fails.
 */
"""

import importlib
import io
import os
import sys
import time
from pathlib import Path

from utils import (
    PLUGIN_INIT_WAIT,
    PROFILING_ENABLED_ENV,
    SKIPPED,
    WPEFRAMEWORK_JSONRPC_URL,
    activate_plugin,
    deactivate_plugin,
    log_error,
    log_info,
    log_success,
    log_warning,
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
    "ledindicator": ["org.rdk.LEDControl"],
}

SUITE_PREREQUISITE_CALLSIGNS = {
    "ledindicator": [],
}

SUITE_INIT_MODULES = {
    "ledindicator": None,
}

SUITE_LIFECYCLES = {
    "ledindicator": "per_test",
}


def normalize_suite_name(raw_name):
    return raw_name.strip().replace("_", "").replace("-", "").lower()


def normalize_test_name(raw_name):
    return raw_name.strip().replace("_", "").replace("-", "").lower()


def resolve_selected_tests(suite_name, requested_tests):
    if not requested_tests:
        return list(SUITES[suite_name]["tests"])

    available_tests = SUITES[suite_name]["tests"]
    resolved = []

    for requested in requested_tests:
        requested_norm = normalize_test_name(requested)
        matches = [
            name
            for name in available_tests
            if normalize_test_name(name) == requested_norm
        ]
        if not matches:
            raise ValueError(
                f"Unknown test '{requested}'. Available tests: {available_tests}"
            )
        resolved.extend(matches)

    return resolved


def load_test_cases(suite_name, selected_tests=None):
    suite_config = SUITES[suite_name]
    module_dir = str(suite_config["module_dir"])

    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    test_cases = []
    for module_name in resolve_selected_tests(suite_name, selected_tests):
        module = importlib.import_module(module_name)
        run_fn = getattr(module, "run_test", None)
        if not callable(run_fn):
            module_file = getattr(module, "__file__", "<unknown>")
            exported = [name for name in dir(module) if not name.startswith("__")]
            raise AttributeError(
                f"Module '{module_name}' from '{module_file}' does not expose callable run_test(). "
                f"Exported names: {exported}"
            )
        test_cases.append((module_name, run_fn))

    return suite_config["banner"], test_cases


def run_suite_init(suite_name):
    module_name = SUITE_INIT_MODULES.get(suite_name)
    if not module_name:
        return True

    base_dir = str(BASE_DIR)
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        log_error(f"Init module import failed: {module_name} ({exc})")
        return False

    run_fn = getattr(module, "run_test", None)
    if not callable(run_fn):
        log_error(f"Init module missing run_test(): {module_name}")
        return False

    log_info(f"Running suite initialization: {module_name}.run_test()")
    try:
        ok = run_fn() is True
    except Exception as exc:
        log_error(f"Suite initialization threw exception: {exc}")
        return False

    if ok:
        log_success("Suite initialization completed successfully")
    else:
        log_error("Suite initialization failed")
    return ok


def activate_test_plugins(suite_name):
    callsigns = list(SUITE_PREREQUISITE_CALLSIGNS.get(suite_name, []))
    callsigns.extend(SUITE_PLUGIN_CALLSIGNS.get(suite_name, []))

    activated = []
    for callsign in callsigns:
        log_info(
            f"Auto-activating plugin '{callsign}' "
            f"via curl JSON-RPC at {WPEFRAMEWORK_JSONRPC_URL}"
        )
        if not activate_plugin(callsign):
            log_error(f"Plugin activation failed: {callsign}")
            return False, activated
        activated.append(callsign)
        log_success(f"Plugin activated: {callsign}")
        log_info(
            f"Waiting {PLUGIN_INIT_WAIT}s for plugin to fully initialise..."
        )
        time.sleep(PLUGIN_INIT_WAIT)

    return True, activated


def deactivate_test_plugins(callsigns):
    success = True
    for callsign in reversed(callsigns):
        log_info(f"Auto-deactivating plugin '{callsign}'")
        if deactivate_plugin(callsign):
            log_success(f"Plugin deactivated: {callsign}")
        else:
            log_error(f"Plugin deactivation failed: {callsign}")
            success = False
    return success


def _is_enabled(value):
    return value.lower() in ("1", "true", "yes")


def configure_mw_fallback(mw_fallback):
    if mw_fallback is None:
        os.environ.setdefault("ENABLE_INDICATOR_MW_FALLBACK", "1")
    else:
        os.environ["ENABLE_INDICATOR_MW_FALLBACK"] = (
            "1" if mw_fallback else "0"
        )

    return _is_enabled(
        os.environ.get("ENABLE_INDICATOR_MW_FALLBACK", "0")
    )


def log_suite_configuration(
    lifecycle,
    auto_activate,
    profiling_enabled,
    mw_fallback_enabled,
    selected_test_count,
):
    log_info(f"Plugin lifecycle: {lifecycle}")
    log_info(
        f"Auto plugin activation: {'enabled' if auto_activate else 'disabled'}"
    )
    log_info(f"Plugin initialization wait: {PLUGIN_INIT_WAIT}s")
    log_info(
        f"Timing/profiling output: {'enabled' if profiling_enabled else 'disabled'}"
    )
    log_info(
        f"Indicator MW fallback: {'enabled' if mw_fallback_enabled else 'disabled'}"
    )
    log_info(f"Selected tests: {selected_test_count}")


def run_suite(
    suite_name,
    selected_tests=None,
    profiling_enabled=False,
    mw_fallback=None,
):
    lifecycle = SUITE_LIFECYCLES.get(suite_name)
    if lifecycle != "per_test":
        raise ValueError(
            f"Unsupported lifecycle '{lifecycle}' for suite '{suite_name}'"
        )

    banner, test_cases = load_test_cases(suite_name, selected_tests)
    print(banner)

    os.environ[PROFILING_ENABLED_ENV] = "1" if profiling_enabled else "0"
    mw_fallback_enabled = configure_mw_fallback(mw_fallback)
    auto_activate = (
        os.environ.get("AUTO_ACTIVATE_PLUGINS", "1").lower()
        not in ("0", "false", "no")
    )
    log_suite_configuration(
        lifecycle,
        auto_activate,
        profiling_enabled,
        mw_fallback_enabled,
        len(test_cases),
    )

    passed = 0
    failed = 0
    skipped = 0
    skipped_cases = []
    failed_cases = []
    original_stdout = sys.stdout

    for tc_name, tc_fn in test_cases:
        log_info(f"\n{'='*60}")
        log_info(f"Running: {tc_name}")
        log_info(f"{'='*60}")
        captured = io.StringIO()
        activated_callsigns = []
        result = False
        sys.stdout = captured
        try:
            plugins_ready = True
            if auto_activate:
                plugins_ready, activated_callsigns = activate_test_plugins(
                    suite_name
                )

            if not plugins_ready:
                log_error(
                    "Test setup failed because plugin activation did not complete."
                )
            elif not run_suite_init(suite_name):
                log_error(
                    "Test setup failed because initialization did not complete."
                )
            else:
                try:
                    result = tc_fn()
                except Exception as exc:
                    result = False
                    print(f"EXCEPTION in {tc_name}: {exc}")
        finally:
            try:
                if (
                    auto_activate
                    and not deactivate_test_plugins(activated_callsigns)
                ):
                    log_error("Test cleanup failed")
                    result = False
            finally:
                sys.stdout = original_stdout

        output = captured.getvalue()
        print(output, end="")

        if result == SKIPPED:
            skipped += 1
            skipped_cases.append(tc_name)
            log_warning(f"[SKIP] {tc_name}")
        elif result is True:
            passed += 1
            log_success(f"[PASS] {tc_name}")
        else:
            failed += 1
            failed_cases.append(tc_name)
            log_error(f"[FAIL] {tc_name}")

        time.sleep(1)

    log_info(f"\n{'='*60}")
    log_info(
        f"Suite Summary: {passed} passed, {failed} failed, {skipped} skipped"
    )
    if skipped_cases:
        log_warning(f"Skipped cases: {skipped_cases}")
    if failed_cases:
        log_error(f"Failed cases: {failed_cases}")
    log_info(f"{'='*60}")

    return failed == 0


if __name__ == "__main__":
    import argparse

    test_case_help = "\n".join(
        f"  {suite_name}:\n"
        + "\n".join(f"    {module_name}" for module_name in config["tests"])
        for suite_name, config in SUITES.items()
    )
    parser = argparse.ArgumentParser(
        description="Run LED indicator L3 test suites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 %(prog)s --help\n"
            "  python3 %(prog)s ledindicator       Run all tests\n"
            "  python3 %(prog)s -t ledindicator    Run all tests with timing\n"
            "  python3 %(prog)s ledindicator --test TCID01_Get_LED_State\n"
            "  python3 %(prog)s ledindicator --test TCID01_Get_LED_State "
            "--test TCID02_Get_Supported_LED_States\n"
            "  python3 %(prog)s ledindicator --disable-mw-fallback\n"
            "\n"
            "Testcase IDs / module names (execution order):\n"
            f"{test_case_help}\n"
            "\n"
            "Test selection:\n"
            "  Without --test, all registered tests run in order.\n"
            "  Supply the full module name, not a bare ID such as TCID01.\n"
            "  Repeat --test to run multiple tests in the supplied order.\n"
            "\n"
            "Execution / prompts:\n"
            "  No interactive prompts. Help exits without running tests or contacting services.\n"
            "  LEDControl is activated before each test and deactivated afterwards.\n"
            "  No suite initializer is configured.\n"
            "  AUTO_ACTIVATE_PLUGINS=0 skips automatic activation/deactivation.\n"
            "  A run with only passes and skips succeeds; failures return exit status 1.\n"
            "\n"
            "Middleware fallback:\n"
            "  Enabled by default; an existing ENABLE_INDICATOR_MW_FALLBACK value is preserved.\n"
            "  --enable-mw-fallback or --disable-mw-fallback overrides the environment.\n"
            "  These two options are mutually exclusive.\n"
            "\n"
            "Environment settings:\n"
            "  TARGET_HOST                  Endpoint host (default: 127.0.0.1)\n"
            "  JSONRPC_PORT                 JSON-RPC port (default: 9998)\n"
            "  WPEFRAMEWORK_JSONRPC_URL      Full JSON-RPC URL (highest priority)\n"
            "  JSONRPC_URL                  Fallback full JSON-RPC URL\n"
            "  VCOMPONENT_PORT              vComponent port (default: 8080)\n"
            "  VCOMPONENT_API_URL           Full vComponent postKVP URL override\n"
            "  LEDCONTROL_PLUGIN_INIT_WAIT  Activation wait in seconds (default: 6)\n"
            "  PLUGIN_INIT_WAIT              Shared fallback for the activation wait\n"
        ),
    )
    parser.add_argument(
        "suite",
        help=f"Test suite name. Available: {list(SUITES.keys())}",
    )
    parser.add_argument(
        "-t",
        "--timing",
        action="store_true",
        help="Enable timing output for passed test cases",
    )
    parser.add_argument(
        "--test",
        dest="tests",
        action="append",
        help="Run only the named testcase module. Repeat to run multiple specific tests.",
    )
    fallback_group = parser.add_mutually_exclusive_group()
    fallback_group.add_argument(
        "--enable-mw-fallback",
        dest="mw_fallback",
        action="store_true",
        help="Enable indicator middleware fallback.",
    )
    fallback_group.add_argument(
        "--disable-mw-fallback",
        dest="mw_fallback",
        action="store_false",
        help="Disable indicator middleware fallback.",
    )
    parser.set_defaults(mw_fallback=None)

    args = parser.parse_args()

    suite_arg = normalize_suite_name(args.suite)
    matching = [
        key for key in SUITES if normalize_suite_name(key) == suite_arg
    ]
    if not matching:
        log_error(
            f"Unknown suite '{args.suite}'. Available: {list(SUITES.keys())}"
        )
        sys.exit(1)

    try:
        ok = run_suite(
            matching[0],
            selected_tests=args.tests,
            profiling_enabled=args.timing,
            mw_fallback=args.mw_fallback,
        )
    except (ValueError, AttributeError) as exc:
        log_error(str(exc))
        sys.exit(1)
    sys.exit(0 if ok else 1)
