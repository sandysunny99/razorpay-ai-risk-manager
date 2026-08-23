# Validation-Set Threshold Selection & Response Tier Optimization

**Track**: Razorpay AI Risk Manager  
**Dataset Split**: `evaluation/validation.jsonl` ($N = 300$, Pos = 81, Neg = 219)  
**Partition Hash**: `e7ad48163c6a3b3d0937aa2ccd4e71dd00d6bd38f87d82508bb258b01649f361`  
**Evaluation Script**: `backend/app/evaluation/evaluate_validation.py`  
**CSV Output**: `evaluation/validation_threshold_results.csv`  

---

## 1. Validation Set Empirical Threshold Sweep

| Threshold | TP | FP | TN | FN | Precision | Recall | F1 Score | Accuracy | FPR | Expected Cost ($50\times$) |
|---|---|---|---|---|---|---|---|---|---|---|
| **20.0** | 81 | 0 | 219 | 0 | 100.0% | 100.0% | 1.0000 | 100.0% | 0.0% | ₹0 |
| **25.0** | 81 | 0 | 219 | 0 | 100.0% | 100.0% | 1.0000 | 100.0% | 0.0% | ₹0 |
| **30.0** | 81 | 0 | 219 | 0 | 100.0% | 100.0% | 1.0000 | 100.0% | 0.0% | ₹0 |
| **35.0** | 80 | 0 | 219 | 1 | 100.0% | 98.77% | 0.9938 | 99.67% | 0.0% | ₹5,000 |
| **40.0 (STEP_UP Boundary)** | 75 | 0 | 219 | 6 | 100.0% | 92.59% | 0.9615 | 98.00% | 0.0% | ₹30,000 |
| **45.0** | 64 | 0 | 219 | 17 | 100.0% | 79.01% | 0.8828 | 94.33% | 0.0% | ₹85,000 |
| **50.0 (REVIEW Boundary)** | 60 | 0 | 219 | 21 | 100.0% | 74.07% | 0.8511 | 93.00% | 0.0% | ₹105,000 |
| **55.0** | 53 | 0 | 219 | 28 | 100.0% | 65.43% | 0.7910 | 90.67% | 0.0% | ₹140,000 |
| **60.0** | 51 | 0 | 219 | 30 | 100.0% | 62.96% | 0.7727 | 90.00% | 0.0% | ₹150,000 |
| **65.0** | 49 | 0 | 219 | 32 | 100.0% | 60.49% | 0.7538 | 89.33% | 0.0% | ₹160,000 |
| **70.0** | 49 | 0 | 219 | 32 | 100.0% | 60.49% | 0.7538 | 89.33% | 0.0% | ₹160,000 |
| **75.0 (AUTO_REMEDIATE Boundary)** | **49** | **0** | **219** | **32** | **100.0%** | **60.49%** | **0.7538** | **89.33%** | **0.0%** | **₹160,000** |
| **80.0** | 49 | 0 | 219 | 32 | 100.0% | 60.49% | 0.7538 | 89.33% | 0.0% | ₹160,000 |
| **85.0** | 49 | 0 | 219 | 32 | 100.0% | 60.49% | 0.7538 | 89.33% | 0.0% | ₹160,000 |
| **90.0** | 49 | 0 | 219 | 32 | 100.0% | 60.49% | 0.7538 | 89.33% | 0.0% | ₹160,000 |

---

## 2. Best Validation Thresholds & Multi-Tier Justification

1. **Overall Detection Layer (Threshold = 40.0)**:
   - **Precision**: $100.0\%$
   - **Recall**: **$92.59\%$** (Catches 75 / 81 attacks on validation split)
   - **F1 Score**: **$0.9615$**
   - **Expected Cost**: **₹30,000**
2. **Autonomous Auto-Remediation Layer (Threshold = 75.0)**:
   - **Precision**: **$100.0\%$** ($0$ False Positives)
   - **Recall**: **$60.49\%$** (Immediate token destruction on high-confidence coincidence)
   - **F1 Score**: **$0.7538$**

---

## 3. Proposed Tiered Response Policy Architecture

| Tier | Risk Score Range | Decision Action | Investigation Depth | Policy Guardrail |
|---|---|---|---|---|
| **Tier 0: LOW** | $0 \le \text{Risk} < 35$ | **`ALLOW`** | Level 0: Fast screening | No friction |
| **Tier 1: MONITOR** | $35 \le \text{Risk} < 45$ | **`MONITOR`** | Level 1: Light investigation (Txn, Customer, Device) | Enhanced post-auth telemetry |
| **Tier 2: STEP_UP** | $45 \le \text{Risk} < 65$ | **`STEP_UP_VERIFICATION`** | Level 2: Risk investigation (Card, Token, Velocity) | Simulated 2FA step-up challenge |
| **Tier 3: REVIEW** | $65 \le \text{Risk} < 75$ | **`REVIEW_REQUIRED`** | Level 2: Comprehensive correlation | Escalate to SOC Case Management |
| **Tier 4: AUTO_REMEDIATE**| $\text{Risk} \ge 75$ | **`AUTO_EXECUTE`** | Level 3: Full critical orchestration | Autonomous Gateway Token Revocation |
