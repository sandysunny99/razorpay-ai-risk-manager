# Razorpay AI Risk Manager

**Razorpay AI Risk Manager is a payment‑risk platform that combines transaction risk scoring, merchant‑aware security controls, protected webhooks, policy‑based remediation, and auditable security decisions.**

[![GitHub CI](https://github.com/sandysunny99/razorpay-ai-risk-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/sandysunny99/razorpay-ai-risk-manager/actions)
[![License: Apache‑2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## Problem
Payment processors face sophisticated fraud attacks that require real‑time risk assessment, secure webhook handling, and evidence‑based decision making across multiple merchants.

## Solution
Razorpay AI Risk Manager provides a payment‑risk engine that ingests transaction events, enriches them with contextual evidence, scores risk, applies policy decisions, and remediates automatically while preserving auditability.

## What Makes It Different
- Merchant‑aware webhook registration with per‑merchant HMAC‑SHA‑256 secrets.
- Merchant‑scoped authorization and tenant attribution are enforced in the verified R‑002 webhook path.
- Auditable event and decision metadata.
- Zombie Card Saver detects and mitigates suspicious card‑reuse activity (4/4 tests PASS).
- Verified security controls backed by targeted tests and CI.

## Architecture
![Architecture Diagram](docs/architecture.png)

The system processes transactions through the following pipeline:

1. **Ingestion** – Receive webhook events.
2. **Enrichment** – Correlate with merchant context and historical data.
3. **Risk Scoring** – Deterministic scoring model (optional AI‑based enrichment).
4. **Policy Decision** – Apply configurable policy rules.
5. **Remediation** – Automated actions (e.g., block, flag, alert).
6. **Audit** – Persist decision metadata for review.

## Payment‑Risk Engine
The engine uses deterministic scoring rules and can optionally incorporate LLM‑based enrichment when enabled (developer‑only, not part of production).

## Merchant Attribution & Multi‑Tenant Security
- Merchants register via `POST /admin/merchants/{merchant_id}/webhook-registrations` obtaining a unique `merchant_id`.
- Webhook endpoints are bound to a merchant‑specific secret.
- Merchant‑scoped authorization and tenant attribution are enforced in the verified R‑002 webhook path.

## Razorpay Webhook Security
- **Endpoint registration** per merchant with unique secret.
- **HMAC‑SHA‑256** verification of payloads.
- **Event idempotency using X‑Razorpay‑Event‑Id**.
- **Webhook event/replay handling**.
- **DLP** redaction of sensitive fields before storage.
- **Audit attribution** linking each event to merchant and policy.

## Zombie Card Saver
Detects and mitigates suspicious card‑reuse activity. All 4/4 tests pass.

## Evaluation Results

| Threshold | Recall | Precision | F1   | Accuracy | Expected Cost |
|-----------|--------|-----------|------|----------|----------------|
| T=40      | 88.06% | 100%      | 0.9365 | 97.33%   | ₹40,000 |
| T=75      | 52.24% | 100%      | 0.6863 | 89.33%   | ₹160,000 |

*Controlled synthetic evaluation – not production traffic.*

## Security Validation
- **R‑002**: VERIFIED_COMPLETE
- Targeted R‑002 tests: **8/8 PASS**
- Security regression: **PASS**
- Zombie Card Saver: **4/4 PASS**
- GitHub CI: **PASS** on commit `52b920bf…`
- Final security recheck: **PASS**
- **CodeQL**: analysis completed successfully, but SARIF/alert details could not be independently retrieved with current repository permissions (**FORMALLY_BLOCKED**).

## Technology Stack
- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: React, TypeScript
- **Cache/Queue**: Redis (optional)
- **Observability**: OpenTelemetry
- **Security**: HMAC, JWT RBAC, CSP
- **Containerization**: Docker

## Quick Start
```bash
# Set up Python environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run backend (verified command)
python -m uvicorn backend.app.main:app --reload

# Run tests (verified)
pytest -q \
  backend/tests/test_admin_webhook_registration.py \
  backend/tests/test_controlled_webhook_endpoint.py
```

## Testing
All targeted tests pass:
```bash
pytest -q backend/tests/test_admin_webhook_registration.py backend/tests/test_controlled_webhook_endpoint.py
```

## CI/CD
GitHub Actions run:
- **Ruff** linting
- **Pytest** test suites
- **Security/crypto** checks
- **Integration/E2E** tests
- **Engine/policy** checks
- **CodeQL** analysis (SARIF unavailable)

## Known Limitations
- Evaluation uses synthetic controlled data, not live production traffic.
- **CodeQL** alerts could not be retrieved; analysis is formally blocked.
- **AgentMemory** and **Cybersecurity Skills** are developer‑only references, deferred for production.
- Redis is optional and not required for core functionality.

## Developer Security Tooling
### AgentMemory (developer‑only / optional)
- Provides local hybrid vector store for developer context.
- Runs a local REST server on port **3111** (WSL2 recommended).
- **Never** stores production payment data, PAN, JWTs, or webhook secrets.

### Cybersecurity Skills (developer‑only / reference)
- Selected concepts: `collecting‑indicators‑of‑compromise`, `implementing‑devsecops‑security‑scanning`, `defending‑llms‑with‑guardrails`.
- Available as reference documentation under `docs/security‑skills/`.
- Not a runtime dependency.

## Roadmap
- **Completed**: R‑002 implementation, security regression, CI verification, evaluation.
- **Deferred**: AgentMemory integration (developer‑only), Cybersecurity Skills reference integration.
- **Future**: Formal CodeQL SARIF access, production deployment validation.

## Hackathon Summary
Razorpay AI Risk Manager delivers autonomous payment‑risk analysis with merchant‑aware controls, protected webhooks, policy‑controlled remediation, and auditable decisions. The solution is backed by verified tests, CI, and security evidence, making it a strong candidate for the hackathon evaluation.
