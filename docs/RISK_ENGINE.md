# Razorpay Risk Manager Agent: Risk Scoring Engine & Mathematical Model

## 1. Weighted Composite Risk Formula

The composite risk score is calculated as a normalized value from $0$ to $100$:

$$\text{Composite Risk} = \frac{\sum (S_i \times W_i)}{\sum W_i}$$

Where:
- $S_{\text{txn}}$: Transaction Anomaly Score ($0-100$), Weight = $25.0$
- $S_{\text{exp}}$: Threat & Breach Exposure Score ($0-100$), Weight = $25.0$
- $S_{\text{crd}}$: Card Lifecycle & Expiration Score ($0-100$), Weight = $15.0$
- $S_{\text{tok}}$: Payment Token State & Zombie Score ($0-100$), Weight = $15.0$
- $S_{\text{cust}}$: Customer Profile Risk ($0-100$), Weight = $10.0$
- $S_{\text{merch}}$: Merchant Baseline Risk ($0-100$), Weight = $10.0$

### Critical Coincidence Multiplier:
When high-confidence breach exposure ($\ge 80$), active token presence ($\ge 15$), and high transaction anomaly ($\ge 50$) occur simultaneously, the score is elevated to $\ge 94.0$ (CRITICAL).

---

## 2. Severity Classification Matrix

| Score Range | Severity Tier | System Response |
|---|---|---|
| **$0 - 24$** | `LOW` | Standard authorization permitted; background monitoring |
| **$25 - 49$** | `MEDIUM` | Flagged for post-authorization anomaly review |
| **$50 - 74$** | `HIGH` | Step-up 2FA challenge / SOC priority queue |
| **$75 - 100$** | `CRITICAL` | Autonomous remediation workflow initiated (Token Revocation) |

---

## 3. Explainable Factor Attribution

Every calculation produces a structured list of `FactorItem` records explaining exact point contributions:
```json
{
  "name": "Threat & Breach Exposure",
  "weight": 25.0,
  "score": 96.0,
  "contribution": 24.0,
  "reason": "High-confidence compromise (96%): Found on Telegram/RedLine-Stealer-Dump-08 [stealer_log]"
}
```
This guarantees that risk explanations are mathematically grounded, eliminating LLM hallucinations.
