# Risk Model Validation & Mathematical Proof

**Date**: 2026-08-23T11:36:00+05:30  
**Model Version**: `v2026.08.1`  
**Engine**: `RiskScoringEngine` (`backend/app/engines/risk_scorer.py`)

---

## 1. Mathematical Scoring Formula & Weights

The composite risk score $R \in [0, 100]$ is calculated as a normalized linear combination of 6 discrete risk dimensions, augmented by a coincidence multiplier:

$$R_{\text{raw}} = \frac{\sum_{i=1}^{6} (S_i \times W_i)}{\sum_{i=1}^{6} W_i}$$

| Dimension ($i$) | Risk Factor Name | Default Weight ($W_i$) | Raw Score Range ($S_i$) | Max Contribution |
|---|---|---|---|---|
| **1** | Transaction Anomaly | $25.0$ | $0 - 100$ | $+25.0$ |
| **2** | Threat & Breach Exposure | $25.0$ | $0 - 100$ | $+25.0$ |
| **3** | Card Lifecycle & Expiration | $15.0$ | $0 - 100$ | $+15.0$ |
| **4** | Payment Token State | $15.0$ | $0 - 100$ | $+15.0$ |
| **5** | Customer Risk Profile | $10.0$ | $0 - 100$ | $+10.0$ |
| **6** | Merchant Baseline Risk | $10.0$ | $0 - 100$ | $+10.0$ |
| **Total** | | **$100.0$** | | **$100.0$** |

---

## 2. Boundary Condition & Severity Transition Validation

| Target Score | Lower Bound | Upper Bound | Assigned Severity | System Response | Validated in Tests |
|---|---|---|---|---|---|
| **$0$** | $0.0$ | $24.9$ | `LOW` | Standard Authorization | `test_transaction_risk_clean` |
| **$21.0$** | $0.0$ | $24.9$ | `LOW` | Remediation Verified | `test_golden_demo_scenario_workflow` |
| **$25.0$** | $25.0$ | $49.9$ | `MEDIUM` | Flag for Anomaly Log | `test_risk_scorer_weights_and_severity` |
| **$50.0$** | $50.0$ | $74.9$ | `HIGH` | Step-Up 2FA Challenge | `test_risk_scorer_weights_and_severity` |
| **$75.0$** | $75.0$ | $100.0$ | `CRITICAL` | Autonomous Token Revocation | `test_risk_scorer_weights_and_severity` |
| **$94.0$** | $75.0$ | $100.0$ | `CRITICAL` | Critical Coincidence (Attack) | `test_golden_demo_scenario_workflow` |
| **$100.0$** | $100.0$ | $100.0$ | `CRITICAL` | Complete System Lockdown | Clamped mathematically |

---

## 3. Coincidence Boost Validation

When a transaction exhibits:
1. High-confidence breach exposure match ($S_{\text{exp}} \ge 80.0$)
2. An active payment vault token ($S_{\text{tok}} \ge 15.0$)
3. High transaction anomaly ($S_{\text{txn}} \ge 50.0$)

The composite score is elevated to $\max(R_{\text{raw}}, 94.0)$, triggering immediate policy auto-execution.

---

## 4. Post-Remediation Recalculation Proof

When token `tok_test_123` is revoked:
- $S_{\text{tok}}$ transitions from $15.0 \rightarrow 0.0$ (Liability eliminated).
- $S_{\text{exp}}$ residual risk transitions to $45.0$ (Compromised credential has 0 active vault tokens).
- $S_{\text{txn}}$ transitions to $10.0$ (Historical log preserved).
- Recalculated Composite Score: **$21.0$ (`LOW`)**.
