#!/usr/bin/env python3
"""
AGTS Conformance Test Runner

Runs all test vectors from test_manifest.json against the reference verifier
and reports results.

Usage:
    python run_conformance.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "verifier"))
from agts_verify import (
    VerificationReport,
    verify_envelope,
    verify_bundle,
    verify_merkle_proof_vector,
    verify_boundary_classification,
    detect_type,
)

CONFORMANCE_DIR = os.path.dirname(os.path.abspath(__file__))


def run_test(entry: dict) -> tuple[bool, str]:
    filepath = os.path.join(CONFORMANCE_DIR, entry["file"])
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Failed to load: {e}"

    report = VerificationReport()
    doc_type = detect_type(data)

    if doc_type == "envelope":
        profile = data.get("policy_profile")
        verify_envelope(data, report, profile)
    elif doc_type == "bundle":
        verify_bundle(data, report)
    elif doc_type == "merkle_proof":
        verify_merkle_proof_vector(data, report)
    elif doc_type == "boundary_classification":
        verify_boundary_classification(data, report)
    else:
        return False, f"Could not detect document type: {doc_type}"

    expected = entry["expected"]

    if expected == "PASS":
        if report.passed:
            return True, "All checks passed as expected"
        else:
            failed = report.failed_checks
            return False, f"Expected PASS but got FAIL: {failed}"
    else:
        if not report.passed:
            failed = report.failed_checks
            expected_failures = entry.get("expected_failures", [])
            if expected_failures:
                missing = [f for f in expected_failures if f not in failed]
                if missing:
                    return False, f"Expected failures {missing} not found in actual failures {failed}"
            return True, f"Correctly detected failures: {failed}"
        else:
            return False, "Expected FAIL but all checks passed"


def main():
    manifest_path = os.path.join(CONFORMANCE_DIR, "test_manifest.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    total = 0
    passed = 0
    failed_tests = []

    print(f"\n{'='*70}")
    print(f"  AGTS V1 Conformance Test Suite")
    print(f"{'='*70}\n")

    for section in ("valid", "invalid"):
        print(f"  --- {section.upper()} vectors ---\n")
        for entry in manifest.get(section, []):
            total += 1
            ok, detail = run_test(entry)
            status = "\u2713 PASS" if ok else "\u2717 FAIL"
            print(f"  {status}  {entry['file']}")
            print(f"         {entry['description']}")
            print(f"         {detail}\n")
            if ok:
                passed += 1
            else:
                failed_tests.append(entry["file"])

    print(f"{'='*70}")
    overall = "PASS" if passed == total else "FAIL"
    print(f"  Result: {overall} — {passed}/{total} tests passed")
    if failed_tests:
        print(f"  Failed: {', '.join(failed_tests)}")
    print(f"{'='*70}\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
