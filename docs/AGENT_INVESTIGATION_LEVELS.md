# Agent Investigation Levels & Dynamic Tool Selection Architecture

## 1. Investigation Level Hierarchy

The Razorpay Risk Manager Agent does not execute a monolithic, brute-force script for every transaction. Instead, it dynamically calibrates its investigation depth based on incoming parameters, behavioral velocity, and risk tiering:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Level 0: Fast-Path Screening (Clean Traffic, Risk < 35)                 │
│ - Tools: get_transaction, get_card, get_customer, evaluate_txn_risk   │
│ - Skips: check_card_exposure, evaluate_token_risk, create_case        │
└────────────────────────────────────────────────────────────────────────┘
                                    │ (Score >= 35 or Velocity >= 2)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Level 1: Baseline Telemetry Monitoring (35 <= Risk < 40)              │
│ - Tools: Fast-path tools + evaluate_card_risk + write_audit           │
│ - Focus: Flagging velocity variance for post-auth telemetry            │
└────────────────────────────────────────────────────────────────────────┘
                                    │ (Score >= 40 or Geo / Device Mismatch)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Level 2: Targeted Evidence Gathering & Step-Up (40 <= Risk < 75)       │
│ - Tools: check_card_exposure + request_step_up_challenge + create_case│
│ - Focus: 2FA challenge execution or SOC case escalation               │
└────────────────────────────────────────────────────────────────────────┘
                                    │ (Score >= 75 or Zombie Token)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Level 3: Autonomous Deep Remediation & Verification (Risk >= 75)      │
│ - Tools: execute_revoke_token + verify_and_recalculate + create_case  │
│ - Focus: Gateway token destruction, vault state check, risk drop verification │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Dynamic Tool Selection & Skipped Reasons Matrix

| Tool Name | Tool Purpose | Selected Conditions | Skipped Condition & Reason Logged |
| :--- | :--- | :--- | :--- |
| `get_transaction` | Initial entity retrieval | Always executed | Never skipped |
| `get_card` | Masked PAN & BIN lookup | Always executed | Never skipped |
| `get_customer` | Baseline profile comparison | Always executed | Never skipped |
| `get_token` | Vault token state lookup | `txn.token_id is not None` | *"No token_id present on transaction record; skipping token lookup."* |
| `evaluate_transaction_risk` | Velocity, amount & geo check | Always executed | Never skipped |
| `check_card_exposure` | Dark-web & stealer CTI lookup | Velocity $\ge 3$, Amount $\ge ₹15k$, Cross-border, or Score $\ge 35$ | *"Clean domestic transaction below anomaly threshold; skipping heavy CTI lookups."* |
| `evaluate_card_risk` | Expiry & fraud history check | Always executed | Never skipped |
| `evaluate_token_risk` | Zombie token & lifecycle check | `token is not None` | *"No token present on transaction."* |
| `calculate_composite_risk` | 6-factor mathematical score | Always executed | Never skipped |
| `execute_revoke_token` | Autonomous gateway token destruction | `response_tier == 'AUTO_REMEDIATE'` | *"Risk below auto-remediation threshold (75.0); revocation withheld."* |
| `verify_and_recalculate` | Vault API state check & recalculation | Executed post-revocation | *"No autonomous remediation executed; verification not required."* |
| `request_step_up_challenge`| Simulated 2FA challenge | `response_tier == 'STEP_UP'` | *"Transaction risk does not require step-up challenge."* |
| `create_case` | SOC Security case creation | Initial Risk $\ge 40.0$ or Zombie | *"Low risk / clean transaction; skipping case creation."* |
| `write_audit` | Tamper-evident hash ledger write | Always executed | Never skipped |

---

## 3. Tool Selection Audit Schema

Every investigation returns a structured `tool_audit` array:
```json
{
  "tool_audit": [
    {
      "tool": "get_transaction",
      "selected": true,
      "reason": "Initial transaction entity retrieval required for risk screening."
    },
    {
      "tool": "check_card_exposure",
      "selected": false,
      "reason": "Clean domestic transaction below anomaly threshold; skipping heavy CTI lookups."
    },
    {
      "tool": "execute_revoke_token",
      "selected": true,
      "reason": "Autonomous token revocation executed under Policy Rule PR-01."
    }
  ],
  "tools_executed": ["get_transaction", "get_card", "get_customer", "evaluate_transaction_risk", "evaluate_card_risk", "calculate_composite_risk", "write_audit"],
  "tools_skipped": ["check_card_exposure", "get_token", "evaluate_token_risk", "execute_revoke_token", "create_case"]
}
```

This dynamic selection guarantees **low-latency sub-100ms authorization for legitimate shoppers** while providing **deep forensic analysis for compromised entities**.
