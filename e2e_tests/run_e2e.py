"""
Standalone E2E Test Suite Runner for the AI Healthcare System.
Usage:
    python e2e_tests/run_e2e.py
    python e2e_tests/run_e2e.py --tier 1
    python e2e_tests/run_e2e.py --url http://127.0.0.1:8000
    python e2e_tests/run_e2e.py --json-report e2e_report.json
"""
import argparse
import importlib
import inspect
import os
import sys
import time
from pathlib import Path

# Safe terminal encoding reconfiguration
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Configure isolated test database and test flags before importing backend
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite:///./test_e2e_isolated.db"
os.environ["TESTING"] = "1"
os.environ["MICROSERVICES_MODE"] = "false"

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.auth import TestAuthManager
from e2e_tests.harness.reporter import TestReporter


def discover_and_run_tests(
    base_url: str = "",
    target_tier: str = "all",
    target_domain: str = None,
    verbose: bool = False,
    fail_fast: bool = False,
    json_report: str = None,
) -> int:
    reporter = TestReporter()
    tiers_dir = PROJECT_ROOT / "e2e_tests" / "tiers"

    tier_dirs = {
        "1": tiers_dir / "tier1_feature_coverage",
        "2": tiers_dir / "tier2_boundary_corner_cases",
        "3": tiers_dir / "tier3_cross_feature_combinations",
        "4": tiers_dir / "tier4_real_world_scenarios",
    }

    selected_tiers = tier_dirs.keys() if target_tier.lower() == "all" else [target_tier]

    print("\n" + "=" * 80)
    print("  AI HEALTHCARE SYSTEM - E2E TEST SUITE RUNNER")
    print(f"  Target Base URL : {base_url or 'In-Process (FastAPI TestClient)'}")
    print(f"  Selected Tiers  : {', '.join(selected_tiers)}")
    print("=" * 80 + "\n")

    # Seed test users if in-process
    if not base_url:
        TestAuthManager.seed_test_users()

    # Common clients
    admin_token = TestAuthManager.generate_token(username="admin_e2e", role="admin", user_id=1, facility_id=1)
    doctor_token = TestAuthManager.generate_token(username="doctor_e2e", role="doctor", user_id=2, facility_id=1)
    nurse_token = TestAuthManager.generate_token(username="nurse_e2e", role="nurse", user_id=3, facility_id=1)
    patient_token = TestAuthManager.generate_token(username="patient_e2e", role="patient", user_id=4, facility_id=1)

    clients = {
        "e2e_client": E2EClient(base_url=base_url),
        "admin_client": E2EClient(base_url=base_url, auth_token=admin_token),
        "doctor_client": E2EClient(base_url=base_url, auth_token=doctor_token),
        "nurse_client": E2EClient(base_url=base_url, auth_token=nurse_token),
        "patient_client": E2EClient(base_url=base_url, auth_token=patient_token),
    }

    for tier_key in sorted(selected_tiers):
        tdir = tier_dirs.get(tier_key)
        if not tdir or not tdir.exists():
            continue

        test_files = sorted(tdir.glob("test_*.py"))
        for tfile in test_files:
            domain_name = tfile.stem.replace("test_", "")
            if target_domain and target_domain.lower() not in domain_name.lower():
                continue

            rel_module = f"e2e_tests.tiers.{tdir.name}.{tfile.stem}"
            try:
                mod = importlib.import_module(rel_module)
            except Exception as exc:
                reporter.record(
                    name=tfile.name,
                    tier=f"tier{tier_key}",
                    domain=domain_name,
                    status="ERROR",
                    error=f"Failed to import {rel_module}: {exc}",
                )
                print(f"  [ERROR] [{tdir.name}] {tfile.name}: {exc}")
                continue

            # Find all test functions
            test_funcs = [
                (name, fn)
                for name, fn in inspect.getmembers(mod, inspect.isfunction)
                if name.startswith("test_")
            ]

            for test_name, test_func in test_funcs:
                sig = inspect.signature(test_func)
                call_args = {}
                for param in sig.parameters.values():
                    if param.name in clients:
                        call_args[param.name] = clients[param.name]

                t_start = time.perf_counter()
                try:
                    test_func(**call_args)
                    elapsed = (time.perf_counter() - t_start) * 1000.0
                    reporter.record(
                        name=test_name,
                        tier=f"tier{tier_key}",
                        domain=domain_name,
                        status="PASS",
                        duration_ms=elapsed,
                    )
                    if verbose:
                        print(f"  [PASS] [{tdir.name}] {test_name} ({elapsed:.1f}ms)")
                except AssertionError as ae:
                    elapsed = (time.perf_counter() - t_start) * 1000.0
                    reporter.record(
                        name=test_name,
                        tier=f"tier{tier_key}",
                        domain=domain_name,
                        status="FAIL",
                        duration_ms=elapsed,
                        error=str(ae),
                    )
                    print(f"  [FAIL] [{tdir.name}] {test_name}: {ae}")
                    if fail_fast:
                        reporter.print_summary()
                        return 1
                except Exception as ex:
                    elapsed = (time.perf_counter() - t_start) * 1000.0
                    reporter.record(
                        name=test_name,
                        tier=f"tier{tier_key}",
                        domain=domain_name,
                        status="ERROR",
                        duration_ms=elapsed,
                        error=str(ex),
                    )
                    print(f"  [ERROR] [{tdir.name}] {test_name}: {ex}")
                    if fail_fast:
                        reporter.print_summary()
                        return 1

    reporter.print_summary()

    if json_report:
        reporter.save_json(json_report)
        print(f" Saved JSON test report to: {json_report}")

    summary = reporter.summarize()
    return 1 if (summary.failed > 0 or summary.errors > 0) else 0


def main():
    parser = argparse.ArgumentParser(description="AI Healthcare System Standalone E2E Test Runner")
    parser.add_argument("--url", default=os.getenv("E2E_API_URL", ""), help="Target API Base URL (e.g. http://127.0.0.1:8000)")
    parser.add_argument("--tier", default="all", choices=["all", "1", "2", "3", "4"], help="Tier filter (1, 2, 3, 4, or all)")
    parser.add_argument("--domain", default=None, help="Filter tests by domain name substring")
    parser.add_argument("--json-report", default=None, help="Path to write JSON test report")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output showing every test")
    parser.add_argument("-x", "--fast", action="store_true", help="Fail fast on first error")

    args = parser.parse_args()
    exit_code = discover_and_run_tests(
        base_url=args.url,
        target_tier=args.tier,
        target_domain=args.domain,
        verbose=args.verbose,
        fail_fast=args.fast,
        json_report=args.json_report,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
