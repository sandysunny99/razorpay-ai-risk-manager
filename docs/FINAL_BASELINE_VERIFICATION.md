# Final Baseline Verification Record (v2.0.0-rc1)

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Commit Hash**: `66ec201`  
**Branch**: `feature/risk-manager-webapp-security`  
**Timestamp**: 2026-08-23T15:33:00+05:30  
**Working Tree**: Clean (0 uncommitted modifications, 0 debug artifacts)  

---

## 1. Verified Immutable Baseline Checksums & Metrics

- **Target Benchmark File**: `evaluation/test.jsonl` ($N = 300$, 67 Positive, 233 Negative)
- **Frozen Test-Set SHA-256**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`
- **Integrity Verification**: `python scripts/verify_test_set.py` $\rightarrow$ **PASS**

### Measured Empirical Metrics on Frozen Test Set:

```
                                LAYER 1: BROAD DETECTION (T = 40.0)      LAYER 2: AUTONOMOUS ACTION (T = 75.0)
ACTUAL POSITIVE (Pos=67)        TP = 59              FN = 8              TP = 35              FN = 32 (Score 40-74)
ACTUAL NEGATIVE (Neg=233)       FP = 0               TN = 233            FP = 0               TN = 233
```

| Metric Dimension | Layer 1: Broad Detection ($T=40.0$) | Layer 2: Auto-Action ($T=75.0$) | Status / Benchmark |
| :--- | :--- | :--- | :--- |
| **Precision** | **100.00%** ($1.0000$) | **100.00%** ($1.0000$) | 0 False Positives |
| **Recall (Sensitivity)** | **88.06%** (59 / 67 attacks) | **52.24%** (35 / 67 attacks) | Dual operating point balance |
| **Accuracy** | **97.33%** ($0.9733$) | **89.33%** ($0.8933$) | High classification accuracy |
| **False Positive Rate (FPR)**| **0.00%** ($0.0000$) | **0.00%** ($0.0000$) | Zero legitimate checkout disruption |
| **F1 Score** | **0.9365** | **0.6863** | Balanced precision & recall |
| **Illustrative Expected Cost**| **₹40,000** | **₹160,000** | Illustrative model ($C_{FP}=100, C_{FN}=5000$) |

---

## 2. Quality Gate Verification Results

1. **Pytest Suite**: **54 / 54 tests passed (100%)** in $1.88\text{s}$ across 12 test modules.
2. **Pre-Deployment Gate**: `python scripts/pre_deploy.py` $\rightarrow$ **100% (7/7 gates passed)**.
3. **Frontend Production Build**: `npm run build` $\rightarrow$ **1,816 modules transformed, 0 TypeScript errors in 1.15s**.
4. **Cloudflare Telemetry**: `verify_cloudflare_security.py` $\rightarrow$ **PASS** (1–99 bot taxonomy).
5. **Data Protection & DLP**: `verify_data_security.py` $\rightarrow$ **PASS** (AES-256-GCM, Luhn scanner).
