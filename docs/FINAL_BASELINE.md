# Frozen System Baseline & Exact Metric Reproduction

**Hackathon**: Razorpay AI Buildathon 2026  
**Track**: AI Risk Manager  
**Project**: Razorpay Risk Manager Agent  
**Baseline Date**: August 23, 2026  
**Test Set Integrity Status**: VERIFIED & FROZEN (Zero Modification)

---

## 1. Frozen Test Set Verification

- **Test Set Path**: `evaluation/test.jsonl`
- **SHA-256 Checksum**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`
- **Total Test Records**: $N = 300$
- **Ground-Truth Positive (Compromised Credentials)**: $67$ ($22.33\%$)
- **Ground-Truth Negative (Legitimate Transactions)**: $233$ ($77.67\%$)
- **Data Split Integrity**: Zero train/validation/test overlap, verified via HMAC fingerprint hashing.

---

## 2. Exact Empirical Metrics at Operating Points

### Operating Point 1: Broad Detection Layer ($T_{\text{detect}} = 40.0$)
*Purpose: Catch compromised credentials and behavioral anomalies with high sensitivity.*

- **True Positives (TP)**: $59$
- **False Positives (FP)**: $0$
- **True Negatives (TN)**: $233$
- **False Negatives (FN)**: $8$
- **Precision**: **$100.00\%$** ($1.0000$)
- **Recall (Sensitivity)**: **$88.06\%$** ($0.8806$)
- **F1 Score**: **$0.9365$** ($93.65\%$)
- **Specificity**: **$100.00\%$** ($1.0000$)
- **False Positive Rate (FPR)**: **$0.00\%$** ($0.0000$)
- **False Negative Rate (FNR)**: **$11.94\%$** ($0.1194$)
- **Accuracy**: **$97.33\%$** ($0.9733$)
- **Illustrative Expected Cost**: **₹40,000** ($(0 \times ₹100) + (8 \times ₹5,000)$)

### Operating Point 2: Autonomous Auto-Remediation Layer ($T_{\text{action}} = 75.0$)
*Purpose: High-confidence boundary for automated, irreversible gateway token revocation.*

- **True Positives (TP)**: $35$
- **False Positives (FP)**: $0$
- **True Negatives (TN)**: $233$
- **False Negatives (FN)**: $32$ (Sub-critical anomalies scoring $40.0 - 74.9$)
- **Precision**: **$100.00\%$** ($1.0000$)
- **Recall (Autonomous Action Sensitivity)**: **$52.24\%$** ($0.5224$)
- **F1 Score**: **$0.6863$** ($68.63\%$)
- **Specificity**: **$100.00\%$** ($1.0000$)
- **False Positive Rate (FPR)**: **$0.00\%$** ($0.0000$)
- **False Negative Rate (FNR)**: **$47.76\%$** ($0.4776$)
- **Accuracy**: **$89.33\%$** ($0.8933$)
- **Illustrative Expected Cost**: **₹160,000** ($(0 \times ₹100) + (32 \times ₹5,000)$)

---

## 3. Comparison of Operating Points

| Metric Dimension | Layer 1: Detection ($T=40.0$) | Layer 2: Auto-Action ($T=75.0$) | Practical Difference & Impact |
| :--- | :--- | :--- | :--- |
| **Operating Objective** | Broad Risk Discovery | Autonomous Token Revocation | High sensitivity vs Zero false action |
| **Precision** | **100.00%** | **100.00%** | Both operating points avoid false accusations |
| **Recall** | **88.06%** (59 / 67) | **52.24%** (35 / 67) | Detection catches 24 additional attacks |
| **F1 Score** | **0.9365** | **0.6863** | Detection maximizes multi-signal coverage |
| **False Positive Rate**| **0.00%** | **0.00%** | Zero disruption to clean transactions |
| **Sub-Critical Routing**| Routed to Step-Up / Review | N/A (Withheld from auto-action) | Progressive defense without drop-off |
| **Expected Cost** | **₹40,000** | **₹160,000** | ₹120,000 illustrative liability reduction |

---

## 4. Test Suite Baseline Execution

```
====================== 39 passed, 1941 warnings in 1.23s ======================
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
```

---

## 5. Frontend Production Build Baseline

```
> tsc -b && vite build
✓ 1814 modules transformed.
dist/index.html                   0.45 kB │ gzip:  0.29 kB
dist/assets/index-DbKCJHtE.css   25.42 kB │ gzip:  5.49 kB
dist/assets/index-DwD4KBbF.js   264.03 kB │ gzip: 75.35 kB
✓ built in 1.80s
```
