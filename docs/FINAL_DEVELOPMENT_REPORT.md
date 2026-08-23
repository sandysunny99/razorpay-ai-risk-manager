# Razorpay AI Risk Manager: Final Development & Verification Report

**Track**: AI Risk Manager  
**Target Event**: Razorpay AI Buildathon 2026  
**Date**: August 23, 2026  
**Status**: Production Ready & Fully Verified

---

## 1. Project Overview

The **Razorpay Risk Manager Agent** is an end-to-end autonomous payment risk investigation and defensive mitigation platform. It continuously evaluates transaction anomalies, card exposure across external dark-web threat feeds, payment token lifecycles (including zombie token detection), and merchant baselines.

The system is governed by a **Two-Layer Tiered Risk Architecture**:
- **Layer 1: Broad Risk Detection Layer ($T = 40.0$)**: Optimized for **High Recall ($92.59\%$ on validation, $88.06\%$ on test set)** to identify compromised cards and credentials.
- **Layer 2: Autonomous Auto-Remediation Layer ($T = 75.0$)**: Optimized for **100.0% Precision ($0$ False Positives)** to authorize irreversible gateway token revocation strictly on multi-signal coincidence.
- **Sub-Critical Progressive Defense ($40.0 - 74.9$)**: Non-destructive Step-Up 2FA Challenge (Tier 2) and SOC Security Case Escalation (Tier 3).

---

## 2. Quantitative Empirical Results Summary

### Held-Out Test Set Results ($N = 300$, Positive = 67, Negative = 233)
- **Test Set SHA-256 Hash**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`
- **True Positives (TP)**: 35
- **False Positives (FP)**: 0
- **True Negatives (TN)**: 233
- **False Negatives (FN)**: 32 (Sub-critical anomalies scoring 40.0 - 74.0)
- **Precision**: **100.00%**
- **Recall at Threshold 75.0**: **52.24%**
- **Recall at Detection Threshold 40.0**: **88.06%** (59 of 67 attacks caught)
- **F1 Score**: **0.6863**
- **False Positive Rate (FPR)**: **0.00%**
- **Accuracy**: **89.33%**
- **Expected Cost ($C_{FP}=₹100, C_{FN}=₹5,000$)**: ₹160,000 (Drops to ₹40,000 with Step-Up verification)

### Validation Set Results ($N = 300$, Positive = 81, Negative = 219)
- **True Positives (TP)**: 49 (Threshold 75) / 75 (Threshold 40)
- **False Positives (FP)**: 0
- **True Negatives (TN)**: 219
- **Precision**: **100.00%**
- **Recall at Detection Threshold 40.0**: **92.59%**

---

## 3. Architecture & Security Capabilities

1. **Deterministic Multi-Factor Scoring**: Weighted 6-dimension risk model (Transaction, CTI Exposure, Card Status, Token State, Customer Profile, Merchant Baseline).
2. **Deterministic Policy & Guardrail Engine**:
   - Token auto-revocation allowed ONLY at $\ge 75.0$ or Zombie Token.
   - Card suspension requires human approval (`REVIEW_REQUIRED`).
   - Financial transfers are strictly prohibited (`NEVER_EXECUTE`).
3. **Dynamic Agent Investigation (Levels 0 - 3)**:
   - Level 0 Fast-Path Screening (skips heavy CTI for clean low-risk transactions).
   - Level 1 Telemetry Monitoring (moderate baseline variance).
   - Level 2 Step-Up 2FA & Case Review (sub-critical anomalies).
   - Level 3 Deep Remediation & Post-Action State Verification (critical attacks).
4. **Action & Gateway State Verification**: Direct Razorpay Vault API state verification (`REVOKED`), recalculating composite risk ($94.0 \rightarrow 27.0$).
5. **Simulated Step-Up Challenge (2FA/OTP)**: API endpoints `/api/v1/risk/step-up/request` and `/api/v1/risk/step-up/verify`, with mathematical score damping ($62 \rightarrow 34$).
6. **Security & Cryptography**:
   - `HMAC-SHA-256 PAN Fingerprinting` (deterministic correlation with zero raw PAN storage).
   - `PCI-Aware DLP Masking & Luhn Validation`.
   - `Tamper-Evident SHA-256 Hash-Chained Audit Ledger`.
   - `Multi-Tenant IDOR Protection & Merchant Scoping`.
   - `Untrusted Threat Input Sanitization`.

---

## 4. Test & Build Verification Summary

- **Backend Pytest Suite**: **39 passed** (0 failures, 0 regressions).
- **Agent Trajectory Benchmark**: **100 dynamic scenarios** across 4 distinct archetype paths $\rightarrow$ **100% completion rate, 100% policy decision correctness**.
- **Frontend Production Build**: **Vite & TypeScript compilation passed** ($0$ TS errors).
- **Test Set Gate**: `python scripts/verify_test_set.py` $\rightarrow$ **PASS (Test set untouched)**.

---

## 5. Verification Commands

```bash
# 1. Verify frozen test set hash
python scripts/verify_test_set.py

# 2. Run full backend automated test suite (39 tests)
pytest -v

# 3. Run reproducible final evaluation benchmark
python scripts/run_final_evaluation.py

# 4. Build frontend production assets
cd frontend && npm run build
```
