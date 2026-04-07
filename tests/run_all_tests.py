#!/usr/bin/env python3
"""
run_all_tests.py
================
Master runner for the PropScan test suite.
Runs every test file in order and prints a consolidated report.

Usage (from project root):
    python tests/run_all_tests.py

    # Skip integration tests (no FastAPI/httpx needed):
    python tests/run_all_tests.py --unit-only

    # Run ground truth comparison against a real LLM DB:
    python tests/run_all_tests.py --compare path/to/llm_output.db
"""

import sys
import os
import argparse
import unittest
import subprocess
from datetime import datetime
# from typing import Tuple, List
import tempfile

temp_db = tempfile.NamedTemporaryFile(delete=False)
os.environ["DB_PATH"] = temp_db.name

ROOT = os.path.dirname(os.path.abspath(__file__))

UNIT_TESTS = [
    os.path.join(ROOT, "unit", "test_filter_chat.py"),
    os.path.join(ROOT, "unit", "test_db_control.py"),
    os.path.join(ROOT, "unit", "test_preprocessing.py"),
]

INTEGRATION_TESTS = [
    os.path.join(ROOT, "integration", "test_api.py"),
]


def run_file(path: str) -> tuple[int, int, list[str]]:
    """Run a test file via subprocess. Returns (passed, failed, error_lines)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", path, "-v", "--tb=short", "--no-header"],
        capture_output=True, text=True, encoding="utf-8",
    )
    passed = result.stdout.count(" PASSED")
    failed = result.stdout.count(" FAILED") + result.stdout.count(" ERROR")
    errors = []
    if failed:
        for line in result.stdout.splitlines():
            if "FAILED" in line or "ERROR" in line or "AssertionError" in line:
                errors.append(line.strip())
    return passed, failed, errors


def run_ground_truth(llm_db: str):
    gt_script = os.path.join(ROOT, "ground_truth", "compare_to_ground_truth.py")
    gt_db     = os.path.join(ROOT, "ground_truth", "ground_truth.db")

    if not os.path.exists(gt_db):
        print("\n[GT] Seeding ground_truth.db first...")
        seed = os.path.join(ROOT, "ground_truth", "seed_ground_truth.py")
        subprocess.run([sys.executable, seed], check=True)

    print(f"\n[GT] Comparing {llm_db} against ground truth...")
    subprocess.run([sys.executable, gt_script, llm_db])


def main():
    parser = argparse.ArgumentParser(description="PropScan test runner")
    parser.add_argument("--unit-only",  action="store_true", help="Skip integration tests")
    parser.add_argument("--compare",    metavar="LLM_DB",    help="Run ground truth comparison")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  PropScan Test Suite")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    files  = UNIT_TESTS + ([] if args.unit_only else INTEGRATION_TESTS)
    labels = (
        ["[UNIT] filter_chat", "[UNIT] db_control", "[UNIT] preprocessing"] +
        ([] if args.unit_only else ["[INTG] api"])
    )

    total_passed = 0
    total_failed = 0
    summary      = []

    for label, path in zip(labels, files):
        name = os.path.basename(path)
        print(f"\n  {label}  →  {name}")
        print(f"  {'-'*50}")

        if not os.path.exists(path):
            print(f"  ⚠  FILE NOT FOUND: {path}")
            summary.append((label, 0, 0, ["File not found"]))
            continue

        p, f, errs = run_file(path)
        total_passed += p
        total_failed += f
        summary.append((label, p, f, errs))

        status = "✓ ALL PASSED" if f == 0 else f"✗ {f} FAILED"
        print(f"  {status}  ({p} passed, {f} failed)")
        for err in errs[:5]:    # show first 5 failures
            print(f"    → {err}")

    # Final report
    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"  {'─'*50}")
    for label, p, f, _ in summary:
        icon = "✓" if f == 0 else "✗"
        print(f"  {icon}  {label:<28}  {p:2d} passed  {f:2d} failed")
    print(f"  {'─'*50}")
    print(f"  TOTAL:  {total_passed} passed,  {total_failed} failed")
    overall = "ALL PASSED ✓✓" if total_failed == 0 else f"{total_failed} FAILURES ✗"
    print(f"  STATUS: {overall}")
    print(f"{'='*60}")

    # Optional GT comparison
    if args.compare:
        run_ground_truth(args.compare)

    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
