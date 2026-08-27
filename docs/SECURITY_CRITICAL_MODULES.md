# Security‑Critical Modules

The following files/classes directly handle risk scores, policy decisions, audit logging, and expose these values via the API. They form the security boundary of the Razorpay AI Risk Manager and must be protected, thoroughly tested, and monitored.

| Module | Path | Relevant Functions / Classes |
|--------|------|------------------------------|
| **Risk Agent** | `backend/app/agent/risk_agent.py` | `RiskAgent.process_transaction`, `RiskAgent.evaluate` |
| **Risk Scorer / Engine** | `backend/app/engines/risk_scorer.py` | `RiskScoringEngine.compute_score` |
| **Policy Engine** | `backend/app/engines/policy_engine.py` | `PolicyEngine.classify_risk_tier`, `PolicyEngine.apply_decision` |
| **Audit Ledger** | `backend/app/engines/audit_ledger.py` | `AuditLedger.record_event`, `AuditLedger.hash_event` |
| **API Routers exposing risk_score** | `backend/app/api/routes_risk.py`, `backend/app/api/routes_cards.py`, `backend/app/api/routes_transactions.py` | Route handlers that read/write the `risk_score` field (e.g., line 39 in `routes_risk.py`) |
| **Core Config / Secrets** | `backend/app/core/config.py` | Holds environment‑derived secret keys (must never be indexed by developer tools) |
| **Database Models** | `backend/app/models/*.py` | `RiskRecord`, `AuditEvent` – persist risk scores and audit logs |

All modifications to these modules must pass the supply‑chain audits and be covered by unit/integration tests.
