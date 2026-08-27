# Razorpay Risk Manager Agent: Policy & Guardrail Engine

## 1. The Need for Deterministic Guardrails

Autonomous AI agents in payment systems must never possess unrestricted authority over critical financial and account operations. The **PolicyEngine** acts as a hard security boundary between the LLM's suggested actions and actual execution.

```
LLM Suggestion ("Revoke Token")
              │
              ▼
   [POLICY GUARDRAIL ENGINE]
              │
    ┌─────────┴─────────┐
    ▼                   ▼
AUTO_EXECUTE     REVIEW_REQUIRED
    │                   │
[Execute on Gateway] [Dispatch SOC Queue]
```

---

## 2. Decision Matrix

| Action | Condition | Policy Decision | Execution Status |
|---|---|---|---|
| **Token Revocation** | Risk $\ge 75$ OR Zombie Token = `true` | `AUTO_EXECUTE` | Executed immediately on payment vault |
| **Token Revocation** | Risk $60 - 74$ | `REVIEW_REQUIRED` | Blocked; queued for SOC analyst |
| **Token Revocation** | Risk $< 60$ | `DENIED` | Blocked; threshold not met |
| **Card Suspension** | Any Risk | `REVIEW_REQUIRED` | Blocked; human supervisor review required |
| **Financial Transfer** | Any Request | `NEVER_EXECUTE` | Forbidden by architecture |
| **Security Case / Audit** | Any Incident | `AUTO_EXECUTE` | Recorded immediately |

---

## 3. Merchant Policy Customization

Merchants can configure overrides via `risk_policy`:
```json
{
  "auto_revoke_token": true,
  "auto_suspend_card": false,
  "critical_threshold": 80.0,
  "human_approval_threshold": 60.0,
  "max_transaction_velocity": 5
}
```
If a merchant disables `auto_revoke_token`, the PolicyEngine automatically reroutes all critical token revocations to `REVIEW_REQUIRED`.
