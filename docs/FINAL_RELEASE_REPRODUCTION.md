# Final Release Reproduction & Execution Record (v2.0.0-rc1)

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Commit**: `4609405`  
**Branch**: `feature/risk-manager-webapp-security`  
**Timestamp**: 2026-08-23T16:26:30+05:30  
**Status**: **ALL RELEASE QUALITY GATES PASSED (100%)**  

---

## 1. Actual Command Execution Outputs

### Gate 1: Test Set Hash Immutability Check
```
Checking test set integrity...
Target: C:\Users\sunny\Downloads\RAZAORPAY AI\evaluation\test.jsonl
Expected SHA-256: 76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f
Computed SHA-256: 76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f
[PASS] TEST_SET_INTEGRITY = PASS (Frozen test set is verified & untouched)
```

### Gate 2: Cloudflare Security Verification
```
=================================================================
RAZORPAY AI RISK MANAGER: CLOUDFLARE EDGE VERIFICATION
=================================================================
[PASS] Cloudflare Edge Header Normalization & Ray ID Tracing Verified.
[PASS] Cloudflare Bot Management & Score Classification Verified.
[PASS] Cloudflare Edge Perimeter Telemetry: HEALTHY (TLS 1.3 + WAF Active).
-----------------------------------------------------------------
[SUCCESS] CLOUDFLARE SECURITY PERIMETER VERIFICATION COMPLETE.
=================================================================
```

### Gate 3: Data Security Verification
```
=================================================================
RAZORPAY AI RISK MANAGER: DATA SECURITY VERIFICATION
=================================================================
[PASS] AES-256-GCM Authenticated Encryption & Decryption Verified.
[PASS] Versioned KeyProvider & Rotation Mechanics Verified (Zero Key Leaks).
[PASS] Backend Dynamic Masking (PAN, Email, IP, Token) Verified.
[PASS] DLP Luhn Scrubber & Secret Scanner Verified.
-----------------------------------------------------------------
[SUCCESS] ALL DATA SECURITY & CRYPTOGRAPHIC GATES PASSED.
=================================================================
```

### Gate 4: Release Guard Enforcement
```
======================================================================
RAZORPAY AI RISK MANAGER: RELEASE GUARD
======================================================================
[PASS] Held-Out Test Set SHA-256 Verified: 76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f
[PASS] Dataset Isolation & Schema Checked: 2000 unique transaction records across 3 splits (Zero Leakage)
[PASS] Policy Engine Configuration & Response Boundaries Verified.
----------------------------------------------------------------------
[SUCCESS] ALL RELEASE GUARD CHECKS PASSED. SYSTEM IS READY.
======================================================================
```

### Gate 5: Reproducible Final Evaluation Benchmark ($N=300$)
```
======================================================================
RAZORPAY AI RISK MANAGER: REPRODUCIBLE EVALUATION BENCHMARK
======================================================================
[1] TEST SET IMMUTABILITY CHECK:
    Current SHA-256:  76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f
    Expected SHA-256: 76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f
    --> STATUS: INTEGRITY VERIFIED (Zero test-set modification/leakage)

[2] EMPIRICAL METRICS ON HELD-OUT TEST SET (N = 300):
    True Positives (TP):   35
    False Positives (FP):  0
    True Negatives (TN):   233
    False Negatives (FN):  32
    Precision:             100.00% (0 False Positives)
    Recall (Sensitivity):  52.24%
    Accuracy:              89.33%
    F1 Score:              0.6863
    False Positive Rate:   0.00%
    False Negative Rate:   47.76%
    Expected Cost (INR):   INR 160,000.00
======================================================================
```

### Gate 6: Backend Automated Pytest Suite
```
54 passed, 2083 warnings in 7.70s (100% pass rate)
```

### Gate 7: Frontend Production Bundle
```
✓ 1816 modules transformed.
✓ built in 5.15s (0 TypeScript errors)
```
