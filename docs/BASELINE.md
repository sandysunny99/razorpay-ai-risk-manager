# Baseline Freeze Report

**Date**: 2026-08-23T11:33:00+05:30  
**Git Commit**: `264650c` ("chore: freeze baseline state v1.0.0")  
**Branch**: `master`

---

## 1. System & Environment Baseline

| Dimension | Specification | Status |
|---|---|---|
| **Operating System** | Windows 11 (PowerShell) | Verified |
| **Python Version** | Python 3.12.10 | Verified |
| **Node.js Version** | Node v25.2.1, npm 11.6.2 | Verified |
| **Database** | SQLite 3.x (via SQLAlchemy 2.0.49) | Operational |
| **Backend Framework** | FastAPI 0.141.1 + Uvicorn 0.30.1 + Pydantic 2.13.4 | Operational |
| **Frontend Framework** | React 18.3.1 + Vite 8.2.2 + Tailwind CSS 3.4.1 | Operational |
| **LLM / Agent Layer** | Structured Tool-Calling Agent Loop (Observe $\rightarrow$ Audit) | Operational |
| **Razorpay Adapter** | Test API mode with Mock fallback (`USE_MOCK_RAZORPAY=True`) | Operational |
| **Redis / Queue** | In-process asynchronous event bus (No external Redis dependency) | Operational |

---

## 2. Test Suite Execution Baseline

```text
pytest -v
======================= 15 passed, 37 warnings in 2.40s =======================

Tests Covered:
- test_e2e_agent.py::test_golden_demo_scenario_workflow (PASSED)
- test_policy.py::test_policy_token_revocation_auto_execute (PASSED)
- test_policy.py::test_policy_token_revocation_zombie (PASSED)
- test_policy.py::test_policy_card_suspension_requires_approval (PASSED)
- test_policy.py::test_policy_financial_transfer_strictly_prohibited (PASSED)
- test_risk_engines.py::test_transaction_risk_high_anomaly (PASSED)
- test_risk_engines.py::test_transaction_risk_clean (PASSED)
- test_risk_engines.py::test_zombie_token_detection (PASSED)
- test_risk_engines.py::test_risk_scorer_weights_and_severity (PASSED)
- test_security.py::test_luhn_algorithm_validation (PASSED)
- test_security.py::test_mask_pan (PASSED)
- test_security.py::test_extract_bin (PASSED)
- test_security.py::test_hmac_fingerprint_deterministic (PASSED)
- test_security.py::test_dlp_redaction (PASSED)
- test_security.py::test_sanitize_untrusted_input (PASSED)
```

---

## 3. Frontend Build Baseline

```text
npm run build (in frontend/)
✓ 1812 modules transformed.
dist/index.html                   0.45 kB │ gzip:  0.28 kB
dist/assets/index-DPupax8v.css   22.91 kB │ gzip:  5.10 kB
dist/assets/index-WmsWsccy.js   230.34 kB │ gzip: 69.33 kB
✓ built in 5.98s (0 TypeScript errors)
```

---

## 4. API Endpoints Baseline

| Endpoint | Method | Response Status | Function |
|---|---|---|---|
| `/` | `GET` | 200 OK | Root service health check |
| `/api/v1/risk/overview` | `GET` | 200 OK | Monitored counts & zombie stats |
| `/api/v1/risk/investigate` | `POST` | 200 OK | Agent autonomous investigation |
| `/api/v1/cards` | `GET` | 200 OK | Monitored cards with masked PANs |
| `/api/v1/tokens` | `GET` | 200 OK | Payment token vault inventory |
| `/api/v1/tokens/zombies` | `GET` | 200 OK | Zombie token detector list |
| `/api/v1/tokens/{id}/revoke`| `POST` | 200 OK | Gateway token revocation |
| `/api/v1/cases` | `GET` | 200 OK | SOC Security Case Queue |
| `/api/v1/audit/events` | `GET` | 200 OK | Immutable Audit Ledger |
| `/api/v1/demo/trigger-golden-scenario` | `POST` | 200 OK | 1-Click Golden Scenario |
| `/api/v1/demo/reset-data` | `POST` | 200 OK | Reset & re-seed test DB |

---

## 5. Golden Demo Workflow Baseline Result

- **Target Transaction**: `TXN-2026-9042` (₹18,500 on card `**** **** **** 4921` from Moscow)
- **Initial Risk Score**: `94.0 / 100` (`CRITICAL`)
- **Policy Evaluated**: `AUTO_EXECUTE` for token revocation (`PR-01`); `REVIEW_REQUIRED` for card suspension
- **Action Taken**: `REVOKE_TOKEN (tok_test_123)`
- **Verification Result**: `VERIFIED_SUCCESSFUL` (Query confirmed `REVOKED`)
- **Final Risk Score**: `21.0 / 100` (`LOW`)
- **Security Case Created**: `CASE-2026-XXXX` (Status: `OPEN`)
- **Audit Log Stored**: Cryptographic audit event persisted

---

## 6. Observations & Hardening Roadmap

1. **Audit Ledger**: Currently logs audit records in relational table. We will harden this to a **tamper-evident hash-chained audit log** with verification tooling (`verify_audit_chain()`) to guarantee mathematical tamper detection.
2. **Card Security Documentation**: Update naming to "HMAC-SHA-256 PAN fingerprinting" and "PCI-aware security design".
3. **Multi-Scenario Demo & Failure Handling**: Add dedicated Failure Demo (Action blocked by policy guardrails) and Prompt Injection Demo (Adversarial CTI payload treated strictly as data).
4. **Seed & Reset Scripts**: Create standalone `scripts/seed_demo.py` and `scripts/reset_demo.py` for command-line reproducibility.
