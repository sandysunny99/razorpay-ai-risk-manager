# Development Baseline Lock: WebApp & Cloudflare Security Extension

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Branch**: `feature/risk-manager-webapp-security`  
**Base Commit**: `af77e38ee57edbe71cc6a279cb105ce7f28e6011`  
**Timestamp**: 2026-08-23T14:15:00+05:30  
**Baseline Status**: **LOCKED & VERIFIED (ALL GATES PASSED)**  

---

## 1. Frozen Dataset Integrity & Checksums

- **Held-Out Test Set**: `evaluation/test.jsonl`
- **SHA-256 Checksum**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`
- **Integrity Verification**: `python scripts/verify_test_set.py` $\rightarrow$ **PASS**
- **Release Guard**: `python scripts/release_guard.py` $\rightarrow$ **PASS**
- **Test Corpus Size**: $N = 300$ (67 Compromised Positives, 233 Legitimate Negatives)
- **Data Isolation**: 2,000 unique transaction records across train (1,400), validation (300), and test (300) with zero ID overlap.

---

## 2. Verified Baseline Empirical Metrics

### Layer 1: Broad Risk Detection ($T_{\text{detect}} = 40.0$)
- **True Positives (TP)**: $59$
- **False Positives (FP)**: $0$
- **True Negatives (TN)**: $233$
- **False Negatives (FN)**: $8$
- **Precision**: **$100.00\%$** ($1.0000$)
- **Recall (Sensitivity)**: **$88.06\%$** ($0.8806$)
- **F1 Score**: **$0.9365$**
- **Accuracy**: **$97.33\%$**
- **False Positive Rate (FPR)**: **$0.00\%$**
- **Illustrative Expected Cost**: **₹40,000**

### Layer 2: Autonomous Auto-Remediation ($T_{\text{action}} = 75.0$)
- **True Positives (TP)**: $35$
- **False Positives (FP)**: $0$
- **True Negatives (TN)**: $233$
- **False Negatives (FN)**: $32$ (Sub-critical anomalies routed to Tier 2 Step-Up / Tier 3 Review)
- **Precision**: **$100.00\%$** ($1.0000$, $0$ False Positives)
- **Recall**: **$52.24\%$** ($0.5224$)
- **F1 Score**: **$0.6863$**
- **Accuracy**: **$89.33\%$**
- **False Positive Rate (FPR)**: **$0.00\%$**
- **Illustrative Expected Cost**: **₹160,000**

---

## 3. Automated Test Suite Execution Baseline

```
====================== 45 passed, 2048 warnings in 1.81s ======================
- backend/tests/test_adversarial_threat.py (3 passed)
- backend/tests/test_agent_benchmark.py (1 passed - 100 dynamic scenarios)
- backend/tests/test_audit_chain.py (3 passed)
- backend/tests/test_e2e_agent.py (1 passed)
- backend/tests/test_evaluation_metrics.py (5 passed)
- backend/tests/test_multi_tenancy.py (4 passed)
- backend/tests/test_policy.py (9 passed)
- backend/tests/test_risk_engines.py (4 passed)
- backend/tests/test_security.py (6 passed)
- backend/tests/test_tiered_response.py (2 passed)
- backend/tests/test_two_layer_metrics.py (6 passed)
```

---

## 4. Frontend Production Build Baseline

```
> tsc -b && vite build
✓ 1814 modules transformed.
dist/index.html                   0.45 kB │ gzip:  0.29 kB
dist/assets/index-BhH_rd_K.css   25.38 kB │ gzip:  5.48 kB
dist/assets/index-s9yrEFRM.js   265.70 kB │ gzip: 75.48 kB
✓ built in 1.64s
```
