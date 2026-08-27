# Changelog

All notable changes to the **Razorpay AI Risk Manager** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] — 2026-08-27

### Added
- **OpenTelemetry Distributed Tracing** (`backend/app/core/telemetry.py`): Full span instrumentation for `risk.agent.evaluate`, `cti.lookup`, `razorpay.token.revoke`, and `audit.ledger.append` with optional OTLP export and local tracing fallback.
- **Multi-Tenant Row-Level Database Isolation** (`backend/app/models/entities.py`, `backend/app/core/database.py`): Strict `merchant_id` row-level scoping on audit events and risk assessments with automated SQLite migration helper.
- **Live Razorpay Webhook Receiver** (`backend/app/api/routes_webhook.py`): Real-time endpoint with HMAC-SHA256 signature verification and background task event routing (`payment.captured`, `payment.failed`, `payment.dispute.created`, `token.expired`).
- **SOC Evolution UI Redesign**:
  - `ThreatFeedPanel`: Real-time sliding threat intelligence feed sidebar.
  - `RiskHeatmap`: 10×10 interactive transaction matrix with dynamic forensic inspector.
  - `InvestigationTimeline`: Upgraded 8-phase vertical stepper with icons, expandable telemetry, and copyable SHA-256 block hashes.
  - Global Threat Level Bar in `Header`: Dynamic threat status with animated score transitions.
  - `CommandPalette` (`⌘K` / `Ctrl+K`): Instant fuzzy/substring search across cards, scenarios, alerts, and audit events.
  - `useKeyboardShortcuts`: Hotkeys for fast SOC terminal operations (`⌘K`, `⌘D`, `⌘R`, `1-4`, `?`, `ESC`).
- **CodeQL Automated SAST Workflow** (`.github/workflows/codeql.yml`): Continuous security analysis across Python and JavaScript/TypeScript codebases.
- **Test Coverage Gate**: Integrated `pytest-cov` automated coverage reporting and enforcement in CI pipeline.
- **Semantic Release Configuration** (`.releaserc.json`): Automated version lifecycle and release management.

---

## [2.0.0-rc3] — 2026-08-27

### Added
- **OmniSLM NLP Classifier Layer** (`backend/app/engines/nlp_classifier.py`): Optional Small Language Model integration for threat feed classification, DLP PII extraction, and audit log summarization with 100% graceful fallback. Core risk scoring remains completely deterministic.
- **Razorpay Sandbox API Integration** (`backend/app/services/razorpay_client.py`): Official Razorpay Python SDK integration supporting live test order creation and authentic HMAC-SHA256 webhook payload generation.
- **JWT & Role-Based Access Control (RBAC)** (`backend/app/core/auth.py`): Role hierarchy (`viewer` -> `operator` -> `admin`) with signed HS256 tokens and advisory bypass in `DRY_RUN`/demo mode.
- **Enterprise SOC Dark Mode Design Tokens** (`frontend/src/design/tokens.ts`): Unified typography (`JetBrains Mono` / `Inter`), glass-morphism elevations, and risk-semantic color tokens.
- **Interactive UI Components**:
  - `RiskGauge`: Radial score visualizer with policy decision badges.
  - `Skeleton` & `TableSkeleton`: Loading placeholders for tables and KPI cards.
  - `Pagination`: Modular pagination controls for the audit ledger.
  - Animated KPI counters via `react-countup`.
- **Toast Notification Engine** (`useToast` & `ToastContainer`): Accessible `role="alert"` toast notifications replacing all legacy browser dialogs.
- **Pill-Style Tab Navigation**: Multi-subsystem navigation with live indicators and reactive badge counters.

### Fixed
- **BUG-UI-01**: `CardRiskTable` now passes targeted card IDs to the agent investigation workflow rather than hardcoding static IDs.
- **BUG-UI-02**: `ZombieTokenAlerts` and Zombie Card Saver view conditionally render without empty container placeholders.
- **BUG-UI-03**: Replaced all native browser `alert()` invocations across scenarios with non-blocking toast notifications.
- **BUG-UI-04**: Added skeleton loaders across tab views during backend synchronization.
- **BUG-UI-05**: Added global API error interceptor listener in `api.ts` dispatching user-facing error toasts.
- **BUG-UI-06**: Tamper-evident Audit Ledger equipped with full client-side pagination UI.

### Security
- Reinforced HMAC-SHA256 verification and replay protection.
- Hardened `.dockerignore` to preserve frontend build context while protecting test datasets and secrets.
- Pinned Trivy security scanner to `aquasecurity/trivy-action@v0.36.0`.
- All base-layer Debian packages updated to `python:3.12-slim-bookworm`.

---

## [2.0.0-rc2] — 2026-08-26

### Added
- Real-time Server-Sent Events (SSE) stream (`/api/v1/stream/risk-events`).
- Free API integration bridges: `ip-api.com` geo-scoring, `HaveIBeenPwned` v3, `AbuseIPDB`, Upstash Redis rate-limiting, and Sentry error monitoring.
- PostgreSQL production migration framework via Alembic (`backend/alembic`).

### Fixed
- CORS wildcard replaced with strict `ALLOWED_ORIGINS` environment allowlist.
- Replaced all deprecated `datetime.utcnow()` references with timezone-aware `datetime.now(timezone.utc)`.
- CI parallel workflow with Bandit SAST, Ruff linter, and Docker build gates.

---

## [2.0.0-rc1] — 2026-08-25

### Added
- Two-layer risk architecture: Broad Risk Detection + Autonomous Policy Engine.
- 5 Golden Demo scenarios including Zombie Card Saver, Golden Compromise, and Policy Denial.
- Tamper-evident SHA-256 chained hash audit ledger.
- Cloudflare edge security normalization and bot score classification.
