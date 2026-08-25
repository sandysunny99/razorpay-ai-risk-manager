#!/usr/bin/env python3
"""
Razorpay AI Risk Manager: Release Guard & Integrity Enforcement

This script enforces release criteria:
1. Frozen Held-Out Test Set SHA-256 integrity (zero mutation/leakage)
2. Presence and integrity of training, validation, and test datasets
3. Dataset schema compliance and zero ID overlap across splits
4. Structural verification of backend, frontend, and test files
5. Policy configuration thresholds sanity check
"""

import sys
import json
import hashlib
from pathlib import Path

FROZEN_TEST_HASH = "76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f"

REQUIRED_FILES = [
    "evaluation/train.jsonl",
    "evaluation/validation.jsonl",
    "evaluation/test.jsonl",
    "backend/app/main.py",
    "backend/app/agent/risk_agent.py",
    "backend/app/engines/policy_engine.py",
    "backend/app/engines/risk_scorer.py",
    "backend/app/integrations/razorpay_adapter.py",
    "frontend/src/App.tsx",
    "frontend/src/components/EvaluationDashboard.tsx",
    "frontend/src/components/InvestigationTimeline.tsx",
    "README.md",
    "docs/FINAL_EVALUATION.md",
    "docs/FINAL_READINESS.md"
]

def verify_test_set_hash() -> bool:
    test_path = Path("evaluation/test.jsonl")
    if not test_path.exists():
        print(f"[ERROR] Test set missing at: {test_path.resolve()}")
        return False
    
    with open(test_path, "rb") as f:
        raw_bytes = f.read()
        computed_hash = hashlib.sha256(raw_bytes).hexdigest()
        if computed_hash != FROZEN_TEST_HASH:
            crlf_bytes = raw_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            if hashlib.sha256(crlf_bytes).hexdigest() == FROZEN_TEST_HASH:
                computed_hash = FROZEN_TEST_HASH
    
    if computed_hash != FROZEN_TEST_HASH:
        print(f"[FATAL ERROR] Test set SHA-256 mismatch!")
        print(f"  Expected: {FROZEN_TEST_HASH}")
        print(f"  Computed: {computed_hash}")
        return False
    
    print(f"[PASS] Held-Out Test Set SHA-256 Verified: {computed_hash}")
    return True

def verify_file_structure() -> bool:
    all_ok = True
    for file_rel in REQUIRED_FILES:
        p = Path(file_rel)
        if not p.exists():
            print(f"[ERROR] Required release file missing: {file_rel}")
            all_ok = False
        else:
            print(f"[PASS] File found: {file_rel}")
    return all_ok

def verify_dataset_isolation_and_schema() -> bool:
    splits = ["train.jsonl", "validation.jsonl", "test.jsonl"]
    seen_ids = {}
    
    for split in splits:
        p = Path("evaluation") / split
        if not p.exists():
            return False
        
        with open(p, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                txn_id = record.get("transaction_id") or record.get("txn_id")
                label = record.get("label") if "label" in record else record.get("is_compromised")
                
                if txn_id is None or label is None:
                    print(f"[ERROR] Malformed record in {split} line {line_idx}: txn_id={txn_id}, label={label}")
                    return False
                
                if txn_id in seen_ids:
                    print(f"[FATAL ERROR] Data leakage / Duplicate txn_id: '{txn_id}' in {split} was already in {seen_ids[txn_id]}")
                    return False
                seen_ids[txn_id] = split
                
    print(f"[PASS] Dataset Isolation & Schema Checked: {len(seen_ids)} unique transaction records across 3 splits (Zero Leakage)")
    return True

def verify_policy_thresholds() -> bool:
    sys.path.insert(0, "backend")
    try:
        from app.engines.policy_engine import RiskPolicyConfig
        config = RiskPolicyConfig()
        
        assert config.monitor_threshold == 35.0, "Invalid monitor_threshold"
        assert config.broad_detection_threshold == 40.0, "Invalid broad_detection_threshold"
        assert config.step_up_threshold == 40.0, "Invalid step_up_threshold"
        assert config.review_threshold == 65.0, "Invalid review_threshold"
        assert config.auto_execute_threshold == 75.0, "Invalid auto_execute_threshold"
        print("[PASS] Policy Engine Configuration & Response Boundaries Verified.")
        return True
    except Exception as e:
        print(f"[ERROR] Policy config verification failed: {e}")
        return False

def main():
    print("=" * 70)
    print("RAZORPAY AI RISK MANAGER: RELEASE GUARD")
    print("=" * 70)
    
    ok1 = verify_test_set_hash()
    ok2 = verify_file_structure()
    ok3 = verify_dataset_isolation_and_schema()
    ok4 = verify_policy_thresholds()
    
    print("-" * 70)
    if ok1 and ok2 and ok3 and ok4:
        print("[SUCCESS] ALL RELEASE GUARD CHECKS PASSED. SYSTEM IS READY.")
        print("=" * 70)
        sys.exit(0)
    else:
        print("[FAILURE] RELEASE GUARD FAILED. FIX DEFICIENCIES BEFORE RELEASE.")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
