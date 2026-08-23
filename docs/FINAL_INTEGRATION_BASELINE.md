# Final Integration Baseline Lock

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Branch**: `feature/risk-manager-webapp-security`  
**Commit**: `8bc6e8f`  
**Timestamp**: 2026-08-23T14:44:00+05:30  
**Baseline Status**: **LOCKED & VERIFIED (ALL QUALITY GATES PASSED)**  

---

## 1. Frozen Test Set Checksum & Immutability

- **Held-Out Test Set**: `evaluation/test.jsonl` ($N = 300$, 67 Positive, 233 Negative)
- **SHA-256 Checksum**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`
- **Integrity Status**: `python scripts/verify_test_set.py` $\rightarrow$ **PASS (Zero Mutation, Zero Leakage)**

---

## 2. Verified Empirical Metrics Across Operating Points

```
                                LAYER 1: BROAD DETECTION (T = 40.0)      LAYER 2: AUTONOMOUS ACTION (T = 75.0)
ACTUAL POSITIVE (Pos=67)        TP = 59              FN = 8              TP = 35              FN = 32 (Score 40-74)
ACTUAL NEGATIVE (Neg=233)       FP = 0               TN = 233            FP = 0               TN = 233
```

- **Layer 1: Broad Risk Detection ($T_{\text{detect}} = 40.0$)**:
  - **Recall**: **$88.06\%$** ($0.8806$)
  - **Precision**: **$100.00\%$** ($1.0000$, $0$ False Positives)
  - **F1 Score**: **$0.9365$**
  - **Accuracy**: **$97.33\%$**
  - **False Positive Rate (FPR)**: **$0.00\%$**
  - **Illustrative Expected Cost**: **₹40,000**

- **Layer 2: Autonomous Remediation ($T_{\text{action}} = 75.0$)**:
  - **Precision**: **$100.00\%$** ($1.0000$, $0$ False Positives)
  - **Recall**: **$52.24\%$** ($0.5224$)
  - **F1 Score**: **$0.6863$**
  - **Accuracy**: **$89.33\%$**
  - **False Positive Rate (FPR)**: **$0.00\%$**
  - **Illustrative Expected Cost**: **₹160,000**

---

## 3. Automated Backend Test Suite Results

```
====================== 54 passed, 2083 warnings in 1.91s ======================
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
- backend/tests/test_webapp_security.py (9 passed)
```

---

## 4. Frontend Production Build & Pre-Deployment Verification

- `python scripts/release_guard.py` $\rightarrow$ **PASS**
- `python scripts/verify_cloudflare_security.py` $\rightarrow$ **PASS**
- `python scripts/verify_data_security.py` $\rightarrow$ **PASS**
- `python scripts/pre_deploy.py` $\rightarrow$ **PASS (100%)**
- `cd frontend && npm run build` $\rightarrow$ **PASS (1,816 modules, 0 TypeScript errors in 1.15s)**
