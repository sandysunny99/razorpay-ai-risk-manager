# Final Baseline Metrics & Empirical Evaluation Baseline

**Project**: Razorpay AI Risk Manager Agent  
**Track**: AI Risk Manager  
**Dataset Evaluation Split**: `evaluation/test.jsonl` (300 strictly held-out records)  
**Test Set SHA-256**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`  
**Operating Threshold**: 75.0  

---

## 1. Empirical Baseline Metrics ($N = 300$)

| Metric | Raw Ratio | Percentage / Value | Interpretation |
|---|---|---|---|
| **Total Samples** | $300 / 300$ | **300** | Strictly held-out test split |
| **True Positives (TP)** | $35 / 67$ | **35** | Critical compromised attacks detected |
| **False Positives (FP)** | $0 / 233$ | **0** | **Zero False Positives**: No legitimate customer blocked |
| **True Negatives (TN)** | $233 / 233$ | **233** | Clean domestic transactions passed |
| **False Negatives (FN)** | $32 / 67$ | **32** | Sub-critical anomalies ($40 \le \text{Risk} < 75$) |
| **Precision** | $35 / (35 + 0)$ | **100.00%** ($1.0000$) | Zero legitimate transaction disruption |
| **Recall (Sensitivity)** | $35 / (35 + 32)$ | **52.24%** ($0.5224$) | Auto-executes only on high-confidence multi-signal coincidence |
| **Accuracy** | $(35 + 233) / 300$ | **89.33%** ($0.8933$) | Overall test corpus classification accuracy |
| **Specificity** | $233 / (233 + 0)$ | **100.00%** ($1.0000$) | Complete preservation of normal legitimate traffic |
| **False Positive Rate (FPR)** | $0 / (0 + 233)$ | **0.00%** ($0.0000$) | Minimal friction for legitimate payment users |
| **False Negative Rate (FNR)** | $32 / (35 + 32)$ | **47.76%** ($0.4776$) | Missed from auto-remediation (routed to 2FA/Review) |
| **F1 Score** | $\frac{2 \cdot P \cdot R}{P + R}$ | **68.63%** ($0.6863$) | Harmonic balance at strict auto-remediation threshold |
| **Expected Cost** | $(0 \times ₹100) + (32 \times ₹5,000)$ | **₹160,000** | Illustrative cost model ($C_{\text{FP}}=₹100, C_{\text{FN}}=₹5,000$) |

---

## 2. 2x2 Confusion Matrix

```
                               PREDICTED CRITICAL (>=75)      PREDICTED SUB-CRITICAL (<75)
ACTUAL COMPROMISED (Pos = 67)          TP = 35                         FN = 32
ACTUAL LEGITIMATE (Neg = 233)          FP = 0                          TN = 233
```

---

## 3. Verification Commands
```powershell
# Reproduce baseline metrics directly
python -c "import sys; sys.path.insert(0, 'backend'); from app.evaluation.evaluator import ModelEvaluator; ev = ModelEvaluator(); print(ev.evaluate_dataset('test.jsonl'))"
```
