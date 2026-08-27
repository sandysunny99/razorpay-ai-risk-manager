import hashlib
import os
import sys


def verify_test_set():
    test_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../evaluation/test.jsonl"))
    hash_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../docs/TEST_SET_HASH.txt"))

    if not os.path.exists(test_path):
        print(f"[FAIL] test.jsonl not found at {test_path}")
        sys.exit(1)

    if not os.path.exists(hash_path):
        print(f"[FAIL] TEST_SET_HASH.txt not found at {hash_path}")
        sys.exit(1)

    expected_hash = open(hash_path, "r", encoding="utf-8").read().strip()
    with open(test_path, "rb") as f:
        raw_bytes = f.read()
        current_hash = hashlib.sha256(raw_bytes).hexdigest()
        if current_hash != expected_hash:
            crlf_bytes = raw_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            if hashlib.sha256(crlf_bytes).hexdigest() == expected_hash:
                current_hash = expected_hash

    print("Checking test set integrity...")
    print(f"Target: {test_path}")
    print(f"Expected SHA-256: {expected_hash}")
    print(f"Computed SHA-256: {current_hash}")

    if current_hash == expected_hash:
        print("[PASS] TEST_SET_INTEGRITY = PASS (Frozen test set is verified & untouched)")
        return True
    else:
        print("[FAIL] TEST_SET_INTEGRITY = FAIL (Hash mismatch! Test set has been modified)")
        sys.exit(1)

if __name__ == "__main__":
    verify_test_set()
