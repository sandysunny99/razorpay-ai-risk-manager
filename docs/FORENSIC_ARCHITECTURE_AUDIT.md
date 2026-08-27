# Forensic Repository Architecture & Security Audit

**Repository**: `sandysunny99/razorpay-ai-risk-manager`  
**Current Branch**: `main`  
**Latest Commit SHA**: `6681cd1564e88a4796dffaabd8024fe2afb8049f`  
**Audit Timestamp**: 2026-08-27T18:10:00+05:30  
**Auditor**: Senior Staff AI Security & FinTech Architect  
**Objective**: Establish ground-truth baseline of existing codebase, security controls, endpoints, and limitations prior to executing Production Hardening Sprint.

---

## ═══════════════════════════════════════════════════
## SECTION A: EXISTING ARCHITECTURE & REPOSITORY TREE
## ═══════════════════════════════════════════════════

The repository is organized as a unified monorepo hosting a high-performance Python FastAPI backend and a React 19 / TypeScript / Vite frontend:

```
razorpay-ai-risk-manager/
├── .github/
│   └── workflows/
│       ├── ci.yml                     # 5-job CI pipeline (lint, sec, engine, int, build)
│       └── codeql.yml                 # GitHub CodeQL SAST for Python & JS/TS
├── backend/
│   ├── alembic/                       # Alembic migration environment
│   │   ├── env.py                     # Configured for SQLite & PostgreSQL (Render)
│   │   └── versions/
│   │       └── 60faa62647b9_initial_schema.py # Initial migration stub
│   ├── app/
│   │   ├── agent/                     # Autonomous Risk Investigation Agent
│   │   │   ├── prompts.py             # System prompts with untrusted data isolation
│   │   │   ├── risk_agent.py          # 8-phase investigation & reasoning loop
│   │   │   └── tools.py               # Bounded tool registry (L0-L3)
│   │   ├── api/                       # REST & Streaming Endpoints (14 routers)
│   │   │   ├── routes_audit.py        # Audit ledger query & verification
│   │   │   ├── routes_cards.py        # Card inventory & HMAC fingerprinting
│   │   │   ├── routes_cases.py        # SOC security incident cases
│   │   │   ├── routes_demo.py         # Golden attack scenario triggers
│   │   │   ├── routes_evaluation.py   # Benchmark evaluation reports
│   │   │   ├── routes_exposure.py     # CTI breach correlation
│   │   │   ├── routes_health.py       # Liveness, readiness & dependency probes
│   │   │   ├── routes_risk.py         # Transaction scoring & remediation
│   │   │   ├── routes_security.py     # DLP sandbox, crypto status & posture
│   │   │   ├── routes_stream.py       # Server-Sent Events (SSE) stream
│   │   │   ├── routes_tokens.py       # Razorpay token vault operations
│   │   │   ├── routes_webhook.py      # Live Razorpay webhook receiver
│   │   │   ├── routes_webhooks.py     # Adapter webhook receiver with deduplication
│   │   │   └── routes_zombie_cards.py # Zombie Card Saver REST endpoints
│   │   ├── core/                      # Core infrastructure
│   │   │   ├── auth.py                # JWT & RBAC (viewer, operator, admin)
│   │   │   ├── config.py              # Pydantic Settings & environment variables
│   │   │   ├── database.py            # SQLAlchemy engine, session & init_db
│   │   │   ├── security.py            # HMAC-SHA256, AES-256-GCM & Luhn validator
│   │   │   └── telemetry.py           # OpenTelemetry spans & tracing
│   │   ├── db/
│   │   │   └── seed_data.py           # Deterministic demo state seeder
│   │   ├── engines/                   # Specialized risk & security engines
│   │   │   ├── audit_ledger.py        # SHA-256 hash-chained tamper-evident ledger
│   │   │   ├── card_risk.py           # Card velocity & fraud history scoring
│   │   │   ├── exposure_correlation.py# Dark-web CTI cross-domain correlation
│   │   │   ├── nlp_classifier.py      # OmniSLM text classification with fallback
│   │   │   ├── policy_engine.py       # Deterministic authority & NEVER_EXECUTE
│   │   │   ├── risk_scorer.py         # Multi-factor composite risk calculator
│   │   │   ├── token_risk.py          # Vault token lifecycle & age scoring
│   │   │   ├── transaction_risk.py    # Amount, velocity & geo anomaly scoring
│   │   │   └── verification_engine.py # Closed-loop remediation re-verification
│   │   ├── enrichment/                # Threat intelligence adapters
│   │   │   ├── bin_provider.py        # BIN/IIN bank & scheme lookup
│   │   │   ├── enrichment_service.py  # Orchestrated enrichment aggregator
│   │   │   ├── external_apis.py       # IP geolocation & AbuseIPDB client
│   │   │   └── threat_provider.py     # URLhaus & Mock threat feed providers
│   │   ├── events/                    # Event bus & message normalization
│   │   │   ├── event_bus.py           # Async pub/sub event bus
│   │   │   ├── event_deduplicator.py  # In-memory replay & deduplication filter
│   │   │   ├── event_model.py         # Standardized risk event schemas
│   │   │   └── event_normalizer.py    # Heterogeneous webhook normalizer
│   │   ├── integrations/              # External gateway & perimeter adapters
│   │   │   ├── cloudflare_adapter.py  # Cloudflare edge security signal normalizer
│   │   │   └── razorpay_adapter.py    # Mock & test Razorpay vault adapters
│   │   ├── models/
│   │   │   └── entities.py            # SQLAlchemy entity declarations (13 models)
│   │   ├── security/                  # Specialized security subsystems
│   │   │   ├── dlp.py                 # Data Loss Prevention regex & Luhn gate
│   │   │   └── masking.py             # Redaction & masking utilities
│   │   ├── services/
│   │   │   └── razorpay_client.py     # Official Razorpay Python SDK wrapper
│   │   ├── zombie_card_saver/         # Zombie token lifecycle & dependency engine
│   │   │   ├── detector.py            # Card expiration & token state detector
│   │   │   ├── impact_analyzer.py     # Merchant recurring revenue impact
│   │   │   ├── recommendation.py      # Selective remediation decision engine
│   │   │   ├── schemas.py             # Pydantic schemas for zombie lifecycle
│   │   │   ├── service.py             # Orchestrating service facade
│   │   │   └── severity.py            # Multi-parameter severity categorizer
│   │   └── main.py                    # FastAPI entrypoint, middlewares, CSP, static SPA
│   ├── tests/                         # 21 test suites (83 passing tests)
│   └── requirements.txt               # Pinned Python dependencies
├── evaluation/                        # Held-out evaluation benchmark datasets
│   ├── train.jsonl                    # 1,200 training cases
│   ├── validation.jsonl               # 500 validation cases
│   └── test.jsonl                     # 300 FROZEN held-out cases (SHA-256 verified)
├── frontend/                          # React 19 + TypeScript SOC interface
│   ├── src/
│   │   ├── components/                # 21 modular SOC components
│   │   │   ├── AuditTrailTable.tsx    # Tamper-evident ledger UI with hash verify
│   │   │   ├── CommandPalette.tsx     # ⌘K instant search modal
│   │   │   ├── EvaluationDashboard.tsx# Confusion matrix & benchmark metrics
│   │   │   ├── Header.tsx             # Global Threat Meter & mode indicator
│   │   │   ├── InvestigationTimeline.tsx # 8-phase vertical forensic stepper
│   │   │   ├── LiveRiskTable.tsx      # Risk screening stream (Simulation mode)
│   │   │   ├── RiskHeatmap.tsx        # 10×10 interactive transaction matrix
│   │   │   ├── SecurityCenter.tsx     # DLP sandbox & security control posture
│   │   │   ├── ThreatFeedPanel.tsx    # Real-time CTI sliding sidebar
│   │   │   ├── ZombieCardSaverView.tsx# Token dependency graph & remediation
│   │   │   └── ...
│   │   ├── design/                    # Design tokens & typography
│   │   ├── hooks/                     # Keyboard shortcut & toast hooks
│   │   ├── services/api.ts            # Typed Axios/fetch API client
│   │   ├── types/                     # TypeScript domain interfaces
│   │   ├── App.tsx                    # Main layout, 10 SOC tab navigators
│   │   └── main.tsx                   # React root mount
│   ├── package.json                   # React 19, Lucide, Tailwind, Vite 8
│   ├── vite.config.ts                 # Dev server proxy & build configuration
│   └── Dockerfile.frontend            # Standalone Node 24 alpine frontend container
├── scripts/                           # Quality gates & verification tools
│   ├── pre_deploy.py                  # Pre-deployment validation gate
│   ├── release_guard.py               # Immutability & file integrity verification
│   ├── reset_demo.py                  # Deterministic demo database resetter
│   ├── run_final_evaluation.py        # Reproducible benchmark evaluation
│   ├── seed_demo.py                   # Initial mock data seeder
│   ├── test_public_deployment.py      # Remote HTTP & webhook smoke tester
│   ├── verify_cloudflare_security.py  # Cloudflare edge adapter gate
│   ├── verify_data_security.py        # DLP, HMAC & encryption verification gate
│   └── verify_test_set.py             # Cryptographic SHA-256 test set verifier
├── docs/                              # Central technical documentation repository
│   ├── INDEX.md                       # Master navigation index for judges
│   ├── AGENT_DESIGN.md                # 8-phase agent lifecycle architecture
│   ├── API.md                         # Full REST API specification
│   ├── ARCHITECTURE.md                # Component & defense-in-depth architecture
│   ├── DEMO_RECORDING_SCRIPT.md       # 2-minute video recording screenplay
│   ├── DEPLOYMENT.md                  # Docker, Render & Cloudflare deployment guide
│   ├── HACKATHON_DEMO.md              # 5-minute judge demo runbook
│   ├── HACKATHON_STORY.md             # Project narrative, threat model & motivation
│   ├── POLICY_ENGINE.md               # Deterministic policy guardrails & thresholds
│   ├── RISK_ENGINE.md                 # Composite scoring & factor attribution
│   ├── SECURITY_ARCHITECTURE.md       # Comprehensive threat model & trust boundaries
│   └── TESTING.md                     # Testing strategy & coverage documentation
├── Dockerfile                         # Unified multi-stage production container
├── docker-compose.yml                 # Two-service Docker Compose (backend:8000 + frontend:5173)
├── render.yaml                        # Infrastructure-as-Code for Render Cloud + PostgreSQL
├── pyproject.toml                     # Ruff, Bandit & Pytest configuration
├── README.md                          # Master public landing page & judge documentation
├── SECURITY.md                        # Security policy, threat model & disclosures
└── CHANGELOG.md                       # Semantic version history (v2.1.0)
```

---

## ═══════════════════════════════════════════════════
## SECTION B: EXISTING SECURITY CONTROLS
## ═══════════════════════════════════════════════════

1. **HMAC-SHA-256 Zero-Knowledge Card Fingerprinting** (`backend/app/core/security.py`):
   - Computes salted HMAC-SHA256 digests over sanitized PAN strings.
   - Raw PAN is never stored, logged, or emitted in API responses.
   - Pre-validation enforces Luhn modulus-10 checksum before fingerprinting.
   - Masks all credit card references (`**** **** **** 4921`).

2. **Data Loss Prevention (DLP) Gate** (`backend/app/security/dlp.py`):
   - High-speed regex scanners inspect API inputs, agent outputs, and logs.
   - Detects raw PANs, JWT tokens, Bearer tokens, API credentials (`rzp_live_*`, `cf_*`, `sk_*`), database connection strings, and RSA private keys.
   - Automatically sanitizes, masks, and logs DLP violation events to `dlp_events` table.

3. **Cryptographic Data Protection** (`backend/app/core/security.py`):
   - AES-256-GCM authenticated symmetric encryption for sensitive stored attributes.
   - Generates unique 96-bit nonces per encryption.
   - Validates 128-bit authentication tags to prevent ciphertext tampering.

4. **Tamper-Evident SHA-256 Audit Ledger** (`backend/app/engines/audit_ledger.py`):
   - Immutable append-only audit trail.
   - Block hash: `SHA-256(event_id + actor + decision + risk_score + policy + action + verification + details + previous_hash)`.
   - Continuous chain integrity verification API (`/api/v1/audit/verify-chain`).

5. **Deterministic PolicyEngine Authority** (`backend/app/engines/policy_engine.py`):
   - Strict `NEVER_EXECUTE` guardrails: autonomous financial movement (refunds, transfers) is strictly prohibited at code level.
   - Autonomous token revocation requires $T \ge 75.0$ or proven zombie status.
   - Physical card suspension strictly mandates human supervisor review (`REVIEW_REQUIRED`).
   - LLM suggestions are treated as advisory evidence; PolicyEngine has sole execution authority.

6. **Authentication & RBAC** (`backend/app/core/auth.py`):
   - JWT tokens signed with HS256 algorithm.
   - Role hierarchy: `VIEWER` (1) < `OPERATOR` (2) < `ADMIN` (3).
   - In `APP_MODE=demo` or `DRY_RUN=true`, allows advisory fallback with logged warnings.

7. **Webhook Security & Replay Defense** (`backend/app/api/routes_webhooks.py` & `routes_webhook.py`):
   - Cryptographic HMAC-SHA256 signature verification over exact raw request body using constant-time `hmac.compare_digest`.
   - In-memory event deduplication via `event_deduplicator` (`EventDeduplicator`).

8. **Multi-Tenant Row-Level Scoping** (`backend/app/core/database.py`):
   - Tables (`audit_events`, `risk_assessments`, `security_cases`) feature `merchant_id` column.
   - Database queries filter by `merchant_id`.

9. **Security Headers & CSP** (`backend/app/main.py`):
   - Content-Security-Policy (CSP) restricts script sources to `'self'`.
   - `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `Referrer-Policy`.
   - Swagger docs `/docs` and `/redoc` automatically disabled in production (`APP_ENV=production`).

---

## ═══════════════════════════════════════════════════
## SECTION C: EXISTING REST API ENDPOINTS
## ═══════════════════════════════════════════════════

| Route | Method | Auth / Role | Description |
|---|---|---|---|
| `/health` | `GET` | Public | Liveness probe & service status |
| `/api/v1/health/dependencies` | `GET` | Public | Readiness probe for DB, Redis, CTI |
| `/api/v1/risk/evaluate` | `POST` | Authenticated (Operator) | Evaluate transaction risk & trigger agent |
| `/api/v1/risk/assessments` | `GET` | Authenticated (Viewer) | Query risk assessments with tenant scoping |
| `/api/v1/cards` | `GET` | Authenticated (Viewer) | List enrolled cards (masked PANs only) |
| `/api/v1/cards/fingerprint` | `POST` | Authenticated (Operator) | Zero-knowledge HMAC PAN fingerprint lookup |
| `/api/v1/tokens` | `GET` | Authenticated (Viewer) | List active payment tokens |
| `/api/v1/tokens/{token_id}/revoke` | `POST` | Authenticated (Admin) | Manually revoke payment token |
| `/api/v1/cases` | `GET` | Authenticated (Viewer) | List security incident cases |
| `/api/v1/cases/{case_id}/resolve` | `POST` | Authenticated (Operator) | Resolve/dismiss security case |
| `/api/v1/audit/events` | `GET` | Authenticated (Viewer) | Query audit ledger records |
| `/api/v1/audit/verify-chain` | `GET` | Authenticated (Viewer) | Cryptographically verify SHA-256 block chain |
| `/api/v1/demo/scenarios` | `GET` | Public | List deterministic demo scenarios |
| `/api/v1/demo/trigger/{scenario_id}`| `POST` | Authenticated (Operator) | Execute golden attack scenario |
| `/api/v1/demo/reset` | `POST` | Authenticated (Admin) | Reset database to golden baseline |
| `/api/v1/evaluation/benchmark` | `GET` | Authenticated (Viewer) | Retrieve held-out benchmark evaluation metrics |
| `/api/v1/exposure/events` | `GET` | Authenticated (Viewer) | List dark-web CTI exposure events |
| `/api/v1/exposure/scan` | `POST` | Authenticated (Operator) | Trigger breach correlation scan |
| `/api/v1/security/posture` | `GET` | Authenticated (Viewer) | Security controls pass/fail scorecard |
| `/api/v1/security/dlp-sandbox` | `POST` | Authenticated (Operator) | Interactive DLP redactor test sandbox |
| `/api/v1/security/data-protection` | `GET` | Authenticated (Viewer) | Crypto & key status overview |
| `/api/v1/zombie-cards` | `GET` | Authenticated (Viewer) | List zombie cards & dependent token graph |
| `/api/v1/zombie-cards/{id}/remediate`| `POST`| Authenticated (Admin) | Execute selective remediation on zombie card |
| `/api/v1/zombie-cards/stats` | `GET` | Authenticated (Viewer) | Aggregated zombie card risk metrics |
| `/api/v1/webhooks/razorpay` | `POST` | HMAC Webhook | Adapter webhook ingestion with deduplication |
| `/api/v1/razorpay/webhook` | `POST` | HMAC Webhook | Live Razorpay webhook receiver with background worker |
| `/api/v1/stream/events` | `GET` | Public (Demo) | Server-Sent Events (SSE) stream for live updates |

---

## ═══════════════════════════════════════════════════
## SECTION D: EXISTING FRONTEND ROUTES & SOC VIEWS
## ═══════════════════════════════════════════════════

The frontend is a tabbed Single Page Application (SPA) with 10 dedicated views:

1. **Forensic Timeline (`timeline`)**: 8-phase vertical execution stepper displaying autonomous agent lifecycle (Observe → Audit) with risk delta and raw telemetry.
2. **Risk Heatmap Matrix (`heatmap`)**: 10×10 visual transaction matrix categorizing volume by amount and velocity with detail drawer.
3. **Zombie Card Saver (`zombie-saver`)**: Visual graph of active vault tokens linked to expired/cancelled cards with selective remediation actions.
4. **Risk Screening · Simulation (`liverisk`)**: Real-time simulated payment authorization stream with risk scoring and simulation disclosure banner.
5. **Cards & Vault (`cards`)**: Card inventory displaying masked PANs, cardholder aliases, BIN metadata, and HMAC fingerprints.
6. **Security Cases (`cases`)**: Incident response queue for flagged transactions and CTI matches.
7. **Audit Ledger (`audit`)**: Tamper-evident SHA-256 block ledger with pagination and cryptographic integrity verification button.
8. **SOC & DLP Guard (`security`)**: Live security controls audit scorecard and interactive DLP testing sandbox.
9. **Threat Intel & CTI (`exposure`)**: Dark-web stealer log correlation feed, domain reputation, and breach matches.
10. **Model Evaluation (`evaluation`)**: Empirical confusion matrix, ROC-AUC metrics, and threshold tuning comparison ($T=40$ vs $T=75$).

---

## ═══════════════════════════════════════════════════
## SECTION E: EXISTING EXTERNAL INTEGRATIONS
## ═══════════════════════════════════════════════════

| Integration | Adapter Class | Status / Mode | Fallback Behavior |
|---|---|---|---|
| **Razorpay Vault & Orders** | `MockRazorpayAdapter` / `RazorpayTestAdapter` | `TEST_MODE` / `MOCK` | Deterministic local in-memory vault simulation |
| **Cloudflare Perimeter** | `CloudflareAdapter` | `ADAPTER_VALIDATED` | Normalizes edge headers (`CF-Ray`, `cf-ipcountry`, bot score) |
| **URLhaus CTI** | `URLhausProvider` | `REAL_PROVIDER_WITH_FALLBACK` | Queries `urlhaus-api.abuse.ch` with 1800s TTL cache; falls back to `MockThreatProvider` on timeout/network failure |
| **BIN / IIN Lookup** | `BINProvider` | `SYNTHETIC` | In-memory lookup table for Visa, Mastercard, RuPay card ranges |
| **IP Geolocation** | `IPGeoClient` | `REAL_PROVIDER_WITH_FALLBACK` | Queries `ip-api.com` with 45 req/min rate limit; defaults to local heuristics |
| **Sentry Monitoring** | `sentry-sdk` | `CONFIGURED` (Optional) | Initializes only when `SENTRY_DSN` is provided; scrubs all PAN patterns before sending |
| **Redis Rate Limiter** | `slowapi` + `redis` | `CONFIGURED` (Optional) | Uses Redis when `REDIS_URL` is set; defaults to in-memory limiter |

---

## ═══════════════════════════════════════════════════
## SECTION F: EXISTING DEPLOYMENT CONFIGURATION
## ═══════════════════════════════════════════════════

1. **Docker Containerization (`Dockerfile`)**:
   - Multi-stage build:
     - Stage 1: `node:24-alpine` builds React frontend into `/app/frontend/dist`.
     - Stage 2: `python:3.12-slim-bookworm` installs backend dependencies and serves FastAPI with static asset mounting.
   - Built-in `HEALTHCHECK` probe targeting `http://localhost:8000/health`.

2. **Docker Compose (`docker-compose.yml`)**:
   - Service `backend`: Port 8000:8000, unified image, health check.
   - Service `frontend`: Port 5173:5173 using `frontend/Dockerfile.frontend`.

3. **Render Infrastructure (`render.yaml`)**:
   - Web Service: `razorpay-risk-manager` (Docker runtime, region Singapore, health check `/health`).
   - Managed Database: `razorpay-risk-db` (PostgreSQL free tier).
   - Auto-generated secrets: `HMAC_SECRET_KEY`, `MASTER_ENCRYPTION_KEY`.

---

## ═══════════════════════════════════════════════════
## SECTION G: EXISTING TEST COVERAGE
## ═══════════════════════════════════════════════════

The test suite currently contains **83 passed unit/integration tests** across 21 test modules:

| Test File | Tests | Focus Area |
|---|---|---|
| `test_security.py` | 11 | HMAC fingerprinting, AES-256-GCM, Luhn validation, DLP scanning |
| `test_webapp_security.py` | 5 | Rate limiting, CSP headers, correlation IDs, no stack trace leak |
| `test_adversarial_threat.py` | 4 | Prompt injection resistance in threat feeds, malicious input scrubbing |
| `test_multi_tenancy.py` | 6 | Row-level tenant isolation across audit events and risk assessments |
| `test_enrichment_and_webhooks.py` | 5 | CTI providers, URLhaus client, webhook signature verification |
| `test_webhook_live.py` | 4 | Live Razorpay webhook receiver and background task routing |
| `test_risk_engines.py` | 9 | Multi-factor risk calculation, transaction velocity, geo anomaly |
| `test_policy.py` | 6 | PolicyEngine boundaries, NEVER_EXECUTE guardrails, dual thresholds |
| `test_tiered_response.py` | 4 | 5-tier progressive response mapping (ALLOW to AUTO_EXECUTE) |
| `test_two_layer_metrics.py` | 3 | Dual-threshold evaluation ($T=40$ vs $T=75$) |
| `test_agent_benchmark.py` | 3 | End-to-end agent decision quality across held-out evaluation scenarios |
| `test_e2e_agent.py` | 4 | 8-phase autonomous agent lifecycle and verification loop |
| `test_zombie_card_saver.py` | 5 | Zombie token detection, dependency graph, selective remediation |
| `test_audit_chain.py` | 4 | SHA-256 hash chaining, genesis block, tamper detection |
| `test_evaluation_metrics.py` | 3 | Confusion matrix math, precision calculation, 0 FP enforcement |
| `test_rbac_auth.py` | 4 | JWT creation, decoding, role hierarchy enforcement |
| `test_telemetry.py` | 3 | OpenTelemetry spans and context propagation |
| `test_nlp_classifier.py` | 2 | OmniSLM classifier and fallback behavior |
| `test_razorpay_integration.py` | 2 | Razorpay sandbox adapter and webhook generator |
| `test_database.py` | 2 | SQLite and PostgreSQL session connectivity |
| **Total** | **83 passed** | **All tests passing in ~7.2 seconds** |

---

## ═══════════════════════════════════════════════════
## SECTION H: EXISTING CI PIPELINE
## ═══════════════════════════════════════════════════

Pipeline defined in `.github/workflows/ci.yml`:
1. **Job 1 (`static-analysis`)**: Ruff check (Python 3.12), Bandit SAST (0 HIGH issues required), MyPy advisory check.
2. **Job 2 (`test-security`)**: Security, webapp security, adversarial threat, and multi-tenant test suites.
3. **Job 3 (`test-engines`)**: Risk scorer, policy engine, tiered response, two-layer metrics test suites.
4. **Job 4 (`test-integration`)**: Agent benchmark, E2E lifecycle, zombie card saver, audit chain test suites.
5. **Job 5 (`validate-and-build`)**:
   - Test set hash immutability gate (`verify_test_set.py`).
   - Full pytest suite with `--cov=backend/app --cov-fail-under=75`.
   - Final evaluation benchmark (`run_final_evaluation.py`).
   - Release guard enforcement (`release_guard.py`).
   - Cloudflare telemetry gate (`verify_cloudflare_security.py`).
   - Data security & DLP gate (`verify_data_security.py`).
   - Frontend TypeScript strict mode check (`tsc --noEmit`).
   - Frontend production bundle build (`npm run build`).
   - Docker multi-stage build & Trivy CVE scan.
   - Automatic semantic release tagging on version tags.
6. **CodeQL Workflow (`.github/workflows/codeql.yml`)**: Continuous automated SAST scanning for Python and JavaScript/TypeScript.

---

## ═══════════════════════════════════════════════════
## SECTION I: EXISTING KNOWN LIMITATIONS & GAPS
## ═══════════════════════════════════════════════════

1. **Alembic Migrations**:
   - `backend/alembic/` is initialized, but the only version file (`60faa62647b9_initial_schema.py`) has empty `pass` stubs.
   - Database tables are currently bootstrapped at runtime via `init_db()` (`Base.metadata.create_all(bind=engine)`), not via tracked Alembic migration files.
2. **Authentication & Session Wiring**:
   - `backend/app/core/auth.py` contains JWT generation, role hierarchy, and verification.
   - However, the frontend currently bypasses authentication because no dedicated `/api/v1/auth/login` endpoint issues tokens for browser sessions, and the UI lacks a SOC login screen.
3. **Tenant Context Provenance**:
   - Multi-tenancy column `merchant_id` exists on models, but in some routes it is accepted from request bodies or parameters rather than strictly extracted from the authenticated JWT claims.
4. **Webhook Persistence & Idempotency Storage**:
   - Webhook deduplication uses an in-memory TTL set (`EventDeduplicator`). If the server restarts, duplicate webhook IDs could be re-evaluated. Idempotency must be persisted in a database table (`webhook_events`).
5. **Real-Time WebSockets**:
   - Real-time updates currently use Server-Sent Events (`/api/v1/stream/events`). While SSE is functional, standard SOC interfaces benefit from bidirectional, authenticated WebSockets (`/ws/soc`) with reconnection backoff.
6. **Formal Credential & Key Lifecycle**:
   - `KeyMetadata` table exists, but lacks formal state transitions (`CREATED`, `ACTIVE`, `EXPIRING_SOON`, `ROTATING`, `REVOKED`), automated expiry warning checks, and rotation audit triggers.
7. **Public Deployment Evidence**:
   - Render blueprint `render.yaml` is configured, but live cloud provisioning requires the user's Render dashboard connection. Deployment status must strictly reflect `CONFIGURED` / `DEPLOYED` rather than unverified "production-ready" claims.

---

## ═══════════════════════════════════════════════════
## SECTION J: PROPOSED PRODUCTION-HARDENING ROADMAP
## ═══════════════════════════════════════════════════

Following the Master Prompt's phased sequence:

- **Phase 1: Database & Migration Hardening**:
  - Auto-generate complete Alembic migration script covering all 13 existing SQLAlchemy models.
  - Verify `alembic upgrade head` and `alembic downgrade -1` on both SQLite and PostgreSQL.
  - Add `webhook_events` table for persistent webhook idempotency.
- **Phase 2: Authentication & RBAC Hardening**:
  - Add `/api/v1/auth/login` and `/api/v1/auth/me` endpoints returning signed HS256 JWT tokens with `merchant_id` and role claims.
  - Enforce tenant context strictly from authenticated user identity for all tenant-scoped queries and mutations.
  - Add unit tests for cross-tenant data isolation (Tenant A vs Tenant B).
- **Phase 3: Webhook Security & Idempotency Persistence**:
  - Integrate persistent `webhook_events` table with signature, event_id, raw body hash, and timestamp.
  - Add unit tests for replay attacks, malformed signatures, and duplicate events.
- **Phase 4: AI Agent Boundaries & Prompt Injection Hardening**:
  - Expand prompt injection test suite with adversarial jailbreaks.
  - Ensure strict Pydantic output schema validation with fallback to deterministic PolicyEngine on malformed LLM responses.
- **Phase 5: Credential, Key & Certificate Lifecycle**:
  - Implement formal key lifecycle management (`KeyLifecycleManager`) supporting states: `CREATED`, `ACTIVE`, `EXPIRING_SOON`, `ROTATING`, `REVOKED`.
  - Add automated certificate/secret expiration check in health probes.
- **Phase 6: Zombie Card Saver Hardening**:
  - Deepen selective remediation logic (e.g. preserve legitimate recurring tokens on expired cards; auto-revoke tokens on compromised cards).
  - Add comprehensive audit logs for zombie lifecycle events.
- **Phase 7: Real-Time WebSocket Infrastructure**:
  - Implement `/ws/soc` WebSocket endpoint with JWT query-token authentication and tenant room isolation.
  - Add frontend reconnect loop with exponential backoff (1s, 2s, 4s, 8s, 16s, 30s).
- **Phase 8: Frontend Security Center & SOC Login**:
  - Add professional SOC Login page in frontend.
  - Connect Security Center cards to real backend security audit endpoints.
- **Phase 9: Docker & Deployment Verification**:
  - Verify multi-stage Docker image and `docker-compose up` orchestration.
  - Update `test_public_deployment.py` to test authenticated endpoints.
- **Phase 10: CI/CD & Dependency Scanning**:
  - Add `pip-audit` to CI static analysis job for automated CVE vulnerability scanning.
- **Phase 11: Benchmark & Evaluation Verification**:
  - Re-verify frozen test set SHA-256 (`76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`).
  - Generate updated transparent confusion matrix and cost model.
- **Phase 12: Comprehensive Documentation**:
  - Rewrite `README.md` and `SECURITY.md` following Section 27 and 28 structure with truthful status labeling.

---

## ═══════════════════════════════════════════════════
## SECTION K: FILES THAT MUST NOT BE REWRITTEN UNNECESSARILY
## ═══════════════════════════════════════════════════

The following modules contain verified, working, mission-critical logic that **must be preserved and extended—never deleted or rebuilt from scratch**:

1. `evaluation/test.jsonl`: **FROZEN BENCHMARK**. SHA-256 hash `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f` must remain cryptographically untouched.
2. `backend/app/engines/policy_engine.py`: Contains authoritative deterministic policy guardrails and `NEVER_EXECUTE` rules.
3. `backend/app/engines/audit_ledger.py`: Contains proven SHA-256 block hash-chaining mechanism and verification logic.
4. `backend/app/core/security.py`: Contains working HMAC-SHA256 zero-knowledge card fingerprinting and AES-256-GCM encryption.
5. `backend/app/security/dlp.py`: Contains verified regex + Luhn checksum detection patterns.
6. `backend/app/core/telemetry.py`: Contains instrumented OpenTelemetry spans.
7. `backend/app/zombie_card_saver/`: Contains working token dependency graph and multi-parameter severity calculator.
8. `backend/app/engines/risk_scorer.py`: Contains empirical factor weights and multi-factor composite risk calculator.
9. `backend/app/integrations/cloudflare_adapter.py`: Contains edge header normalization and bot classification.
10. `frontend/src/design/tokens.ts`: Contains verified SOC dark mode tokens, typography, and color palettes.

---

**AUDIT CONCLUSION**: The repository has a solid, well-tested foundation (83 passing tests, 0 Ruff errors, 0 Bandit HIGH issues). The planned production hardening will systematically address migrations, JWT session wiring, WebSocket streaming, persistent webhook idempotency, and key lifecycle management without disrupting any existing capabilities.
