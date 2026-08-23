# Release Baseline & Complete Metric Reproduction

**Project**: Razorpay Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Execution Timestamp**: 2026-08-23T13:58:00+05:30  
**Test Set Integrity Status**: VERIFIED & FROZEN (Zero Leakage, Zero Mutation)  

---

## 1. Environment & Dataset Integrity

- **Held-Out Test Set Path**: `evaluation/test.jsonl`
- **SHA-256 Checksum**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`
- **Dataset Size**: $N = 300$ records
- **Class Distribution**:
  - Ground-Truth Positive (Compromised): $67$ ($22.33\%$)
  - Ground-Truth Negative (Legitimate): $233$ ($77.67\%$)
- **Data Split Isolation**: 0 overlapping transaction IDs or card fingerprints across `train.jsonl`, `validation.jsonl`, and `test.jsonl`.

---

## 2. Exact Empirical Metrics Across Operating Points

### Layer 1: Broad Risk Detection Operating Point ($T_{\text{detect}} = 40.0$)
*Operational Objective: Intercept anomalous velocity, credential exposure, and compromised cards with high sensitivity.*

```
                            PREDICTED POSITIVE       PREDICTED NEGATIVE
ACTUAL COMPROMISED (Pos=67)    TP = 59                  FN = 8
ACTUAL LEGITIMATE (Neg=233)    FP = 0                   TN = 233
```

- **True Positives (TP)**: $59$
- **False Positives (FP)**: $0$
- **True Negatives (TN)**: $233$
- **False Negatives (FN)**: $8$
- **Precision**: **$100.00\%$** ($1.0000$)
- **Recall (Sensitivity)**: **$88.06\%$** ($0.8806$)
- **F1 Score**: **$0.9365$**
- **Accuracy**: **$97.33\%$** ($0.9733$)
- **Specificity**: **$100.00\%$** ($1.0000$)
- **False Positive Rate (FPR)**: **$0.00\%$** ($0.0000$)
- **False Negative Rate (FNR)**: **$11.94\%$** ($0.1194$)
- **Illustrative Expected Cost**: **₹40,000** ($(0 \times ₹100) + (8 \times ₹5,000)$)

---

### Layer 2: Autonomous Remediation Operating Point ($T_{\text{action}} = 75.0$)
*Operational Objective: Authorize irreversible autonomous gateway token revocation strictly on multi-signal coincidence.*

```
                            PREDICTED POSITIVE       PREDICTED NEGATIVE
ACTUAL COMPROMISED (Pos=67)    TP = 35                  FN = 32 (Score 40.0 - 74.9)
ACTUAL LEGITIMATE (Neg=233)    FP = 0                   TN = 233
```

- **True Positives (TP)**: $35$
- **False Positives (FP)**: $0$
- **True Negatives (TN)**: $233$
- **False Negatives (FN)**: $32$ (Sub-critical anomalies routed to Step-Up / Review)
- **Precision**: **$100.00\%$** ($1.0000$)
- **Recall (Autonomous Action Sensitivity)**: **$52.24\%$** ($0.5224$)
- **F1 Score**: **$0.6863$**
- **Accuracy**: **$89.33\%$** ($0.8933$)
- **Specificity**: **$100.00\%$** ($1.0000$)
- **False Positive Rate (FPR)**: **$0.00\%$** ($0.0000$)
- **False Negative Rate (FNR)**: **$47.76\%$** ($0.4776$)
- **Illustrative Expected Cost**: **₹160,000** ($(0 \times ₹100) + (32 \times ₹5,000)$)

---

## 3. Automated Backend Test Execution Results

```
====================== 45 passed, 2048 warnings in 1.65s ======================
- backend/tests/test_adversarial_threat.py (3 passed)
- backend/tests/test_agent_benchmark.py (1 passed - 100 dynamic multi-path scenarios)
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

## 4. Frontend Production Build Verification

```
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.2.2 building client environment for production...
transforming...
✓ 1814 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.45 kB │ gzip:  0.29 kB
dist/assets/index-BhH_rd_K.css   25.38 kB │ gzip:  5.48 kB
dist/assets/index-s9yrEFRM.js   265.70 kB │ gzip: 75.48 kB

✓ built in 1.42s
```
