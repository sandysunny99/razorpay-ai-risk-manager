#!/usr/bin/env python3
"""
Razorpay AI Risk Manager: Pre-Deployment Automated Quality Gate Runner

Executes all pre-deployment quality gates:
1. Test-set SHA-256 immutability
2. Complete pytest suite (54 tests)
3. Reproducible final evaluation benchmark
4. Release guard enforcement
5. Cloudflare edge perimeter verification
6. Data security and cryptographic boundary verification
7. Frontend production build compilation
"""

import sys
import subprocess
from pathlib import Path

def run_command(name: str, cmd: list, cwd: str = ".") -> bool:
    print(f"\n[RUNNING] {name}...")
    try:
        res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
        if res.returncode == 0:
            print(f"[PASS] {name} succeeded.")
            return True
        else:
            print(f"[FAIL] {name} failed with exit code {res.returncode}")
            print(res.stdout[-500:] if res.stdout else "")
            print(res.stderr[-500:] if res.stderr else "")
            return False
    except Exception as e:
        print(f"[ERROR] Could not execute {name}: {e}")
        return False

def main():
    print("=" * 75)
    print("RAZORPAY AI RISK MANAGER: PRE-DEPLOYMENT QUALITY GATE")
    print("=" * 75)

    checks = [
        ("Test Set Hash Immutability", [sys.executable, "scripts/verify_test_set.py"], "."),
        ("Backend Automated Test Suite (54 Tests)", ["pytest", "-q"], "."),
        ("Final Evaluation Benchmark", [sys.executable, "scripts/run_final_evaluation.py"], "."),
        ("Release Guard Enforcement", [sys.executable, "scripts/release_guard.py"], "."),
        ("Cloudflare Edge Verification", [sys.executable, "scripts/verify_cloudflare_security.py"], "."),
        ("Data Security & DLP Verification", [sys.executable, "scripts/verify_data_security.py"], "."),
        ("Frontend Production Build", ["npm.cmd" if sys.platform == "win32" else "npm", "run", "build"], "frontend")
    ]

    all_passed = True
    for name, cmd, cwd in checks:
        if not run_command(name, cmd, cwd):
            all_passed = False
            break

    print("\n" + "=" * 75)
    if all_passed:
        print("[SUCCESS] ALL PRE-DEPLOYMENT QUALITY GATES PASSED (100%).")
        print("SYSTEM IS FULLY VALIDATED AND DEPLOYMENT READY.")
        print("=" * 75)
        sys.exit(0)
    else:
        print("[FAILURE] DEPLOYMENT BLOCKED. ONE OR MORE GATES FAILED.")
        print("=" * 75)
        sys.exit(1)

if __name__ == "__main__":
    main()
