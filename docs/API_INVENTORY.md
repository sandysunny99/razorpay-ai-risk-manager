# API Inventory & Endpoint Catalog

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  
**Status**: Comprehensive API Audit & Plan Complete  

---

## 1. Complete API Route Inventory

| Method | Path | Router Module | Auth / Scope | Input Schema | Output Schema | Sensitive Data Treatment | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/risk/screen` | `routes_risk` | Merchant Scoped | `TransactionScreenRequest` | `TransactionScreenResponse` | Masked PAN (`**** 4921`), No secrets | **REUSE** |
| `POST` | `/api/v1/risk/investigate` | `routes_risk` | Merchant Scoped | `InvestigationRequest` | `InvestigationResponse` | Masked PAN, Tool Audit, No secrets | **REUSE** |
| `POST` | `/api/v1/risk/step-up/request`| `routes_risk`| Merchant Scoped | `StepUpChallengeRequest` | `StepUpChallengeResponse` | Challenge ID, No secrets/OTPs stored | **REUSE** |
| `POST` | `/api/v1/risk/step-up/verify` | `routes_risk` | Merchant Scoped | `StepUpVerifyRequest` | `StepUpVerifyResponse` | Recalculated Risk, No credentials | **REUSE** |
| `GET` | `/api/v1/cards` | `routes_cards` | Merchant Scoped | Query params (limit, status) | `List[CardResponse]` | Masked PAN, HMAC Fingerprint | **REUSE** |
| `GET` | `/api/v1/cards/{id}` | `routes_cards` | Merchant Scoped | Path `card_id` | `CardResponse` | Masked PAN, Cardholder Name | **REUSE** |
| `POST` | `/api/v1/cards/{id}/suspend` | `routes_cards` | Analyst Role | Path `card_id`, Reason | `CardResponse` | Policy Review Required, Masked PAN | **REUSE** |
| `GET` | `/api/v1/tokens` | `routes_tokens` | Merchant Scoped | Query params (limit, is_zombie)| `List[TokenResponse]` | Masked Token ID, Gateway State | **REUSE** |
| `POST` | `/api/v1/tokens/{id}/revoke` | `routes_tokens` | Policy / Agent | Path `token_id`, Reason | `TokenResponse` | State Verified on Vault Adapter | **REUSE** |
| `POST` | `/api/v1/tokens/{id}/rotate` | `routes_tokens` | Policy / Agent | Path `token_id` | `TokenResponse` | New Token ID Generated | **REUSE** |
| `GET` | `/api/v1/cases` | `routes_cases` | SOC Analyst | Query params (status, severity)| `List[CaseResponse]` | Masked PAN, Reason, Timeline | **REUSE** |
| `GET` | `/api/v1/cases/{id}` | `routes_cases` | SOC Analyst | Path `case_id` | `CaseResponse` | Full forensic timeline (Masked) | **REUSE** |
| `POST` | `/api/v1/cases/{id}/resolve` | `routes_cases` | SOC Analyst | Path `case_id`, Resolution | `CaseResponse` | Resolution logged to Audit Ledger | **REUSE** |
| `GET` | `/api/v1/audit/events` | `routes_audit` | Auditor Role | Query params (limit, offset) | `List[AuditEventResponse]` | HMAC Chained Hashes (`prev_hash`) | **REUSE** |
| `GET` | `/api/v1/audit/verify` | `routes_audit` | Auditor Role | None | `AuditIntegrityResponse` | Cryptographic SHA-256 Hash Proof | **REUSE** |
| `GET` | `/api/v1/evaluation/metrics` | `routes_evaluation`| Public/Demo | Split, Threshold, Costs | `EvaluationMetrics` | Dual Matrices (T=40 & T=75) | **REUSE** |
| `GET` | `/api/v1/evaluation/ablation`| `routes_evaluation`| Public/Demo | Split, Threshold | `List[AblationItem]` | Multi-Signal Comparison | **REUSE** |
| `GET` | `/api/v1/evaluation/thresholds`|`routes_evaluation`| Public/Demo| Split | `List[ThresholdSweepItem]` | Empirical Operating Curve | **REUSE** |
| `GET` | `/api/v1/evaluation/transactions`|`routes_evaluation`|Public/Demo| Split, Limit, Offset | `PaginatedScoredTransactions`| Scored Stream (Masked PAN) | **REUSE** |
| `GET` | `/api/v1/evaluation/errors` | `routes_evaluation`| Public/Demo | Split, Threshold | `ErrorAnalysisResponse` | Miss Diagnostics (Score 40-74) | **REUSE** |
| `GET` | `/api/v1/evaluation/tiers` | `routes_evaluation`| Public/Demo | Split | `PolicyTierDistribution` | 5 Progressive Response Tiers | **REUSE** |
| `POST` | `/api/v1/demo/scenario/{id}`| `routes_demo` | Demo Role | Path `scenario_id` | `DemoScenarioResponse` | Scenarios 1 to 6 (Masked data) | **REUSE** |
| `POST` | `/api/v1/demo/reset` | `routes_demo` | Admin Role | None | `DemoResetResponse` | Pristine SQLite DB Reset | **REUSE** |
| `GET` | `/api/v1/exposure/events` | `routes_exposure` | Merchant Scoped | Query params (limit, source) | `List[ExposureEventResponse]` | HMAC Fingerprint, Leak Date, CTI | **NEW** |
| `GET` | `/api/v1/exposure/statistics` | `routes_exposure` | Merchant Scoped | None | `ExposureStatisticsResponse` | Monitored vs Exposed metrics | **NEW** |
| `POST` | `/api/v1/exposure/check` | `routes_exposure` | Merchant Scoped | `ExposureCheckRequest` | `ExposureCheckResponse` | Zero raw PAN; accepts fingerprint | **NEW** |
| `GET` | `/api/v1/security/cloudflare/events`| `routes_security`| SOC Analyst | Query params (limit, event_type)| `List[CloudflareEventResponse]` | Sanitized Ray ID, WAF/Bot Action | **NEW** |
| `GET` | `/api/v1/security/data-protection` | `routes_security` | SOC Analyst | None | `DataProtectionStatusResponse` | Encryption, DLP, HMAC, Key states | **NEW** |
| `GET` | `/api/v1/security/health` | `routes_security` | System Health | None | `SecurityHealthResponse` | Subsystem Health Checklist | **NEW** |
| `POST` | `/api/v1/security/dlp/test` | `routes_security` | Security Test | `DLPTestRequest` | `DLPTestResponse` | Synthetic fake PAN detection test | **NEW** |
| `GET` | `/health` | `routes_health` | Public | None | `HealthResponse` | Liveness & Readiness probe | **NEW** |
| `GET` | `/api/v1/health/dependencies` | `routes_health` | Public | None | `DependencyHealthResponse` | DB, Risk Engine, CTI, Cloudflare | **NEW** |

---

## 2. API Security Controls Summary

1. **Strict Input DLP & Masking**: All input payloads pass through regex Luhn validation; raw PANs are blocked or masked before parsing.
2. **Deterministic Role & Tenant Boundary**: Every read/write requires explicit `merchant_id` context.
3. **No Auth Secrets or Secrets in Response**: CVVs, PINs, OTPs, Razorpay secrets, and Cloudflare tokens are strictly omitted from all schemas.
