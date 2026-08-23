# Razorpay Risk Manager Agent: Agentic Architecture & Tool Design

## 1. Single Agent Architecture

Rather than creating complex and fragile multi-agent networks with high token latency, the system implements **ONE unified Risk Manager Agent** equipped with specialized deterministic tools:

```
                      ┌──────────────────────────────────────┐
                      │          RISK MANAGER AGENT          │
                      │     (Autonomous Risk Orchestrator)   │
                      └──────────────────┬───────────────────┘
                                         │ Tool Calling Loop
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
┌──────────────────┐           ┌──────────────────┐           ┌──────────────────┐
│ Entity Tools     │           │ Analytics Tools  │           │ Action Tools     │
│ • get_transaction│           │ • calc_risk      │           │ • check_policy   │
│ • get_card       │           │ • check_exposure │           │ • revoke_token   │
│ • get_token      │           │ • eval_txn_risk  │           │ • create_case    │
│ • get_customer   │           │ • eval_token_risk│           │ • write_audit    │
└──────────────────┘           └──────────────────┘           └──────────────────┘
```

---

## 2. Agent Execution Lifecycle

1. **OBSERVE**: Ingest transaction or alert.
2. **DETECT**: Evaluate deterministic velocity and amount deviations.
3. **INVESTIGATE**: Query card metadata, token age, and customer baseline history.
4. **CORRELATE**: Match HMAC-SHA256 card fingerprint against CTI breach feeds.
5. **REASON**: Synthesize multi-factor risk scores and formulate natural-language reasoning.
6. **ASSESS RISK**: Classify risk severity ($0-100$).
7. **CHECK POLICY**: Verify if recommended actions are permitted under current merchant guardrails.
8. **ACT**: Execute authorized remediation actions (e.g. revoke compromised token).
9. **VERIFY**: Query payment gateway vault status to verify state transition (`REVOKED`).
10. **AUDIT**: Recalculate post-action risk score, persist structured security case, and write immutable audit record.

---

## 3. Tool Calling Protocol & Guarantees

All agent actions pass through `AgentToolRegistry`:
- **Read-Only Tools**: Can be executed dynamically during the investigation phase.
- **Remediation Tools**: Explicitly require a valid policy decision from `PolicyEngine`.
- **Verification Guarantee**: No action is logged as completed without gateway status confirmation.
