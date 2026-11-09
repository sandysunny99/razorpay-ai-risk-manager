# Netvrio audit report (2026-11-09)

Scope: the whole repository on branch `final-hackathon-docs` (new `backend/api` pipeline, legacy `backend/app`, frontend, CI, Docker), plus
open PR #1. Method: read the code paths end to end, ran every gate CI runs, drove the real app in a browser, and wrote a failing test
before each logic fix. Every item below has a regression test unless marked otherwise.

## Findings and fixes

| # | Area | Finding | Impact | Fix | Evidence |
|---|---|---|---|---|---|
| 1 | Security | **Fail-open defaults.** Unset `NETVRIO_ENV` was treated as `test`: tenant identity came from a client header and the webhook HMAC fell back to the public string `dummy_webhook_secret`. | A deployment that forgot one env var accepted forged webhooks for any tenant. | `backend/runtime_env.py`: unset means production. Test mode must be explicit. | Suite runs with explicit `NETVRIO_ENV=test` (conftest); production-mode tests return 501. |
| 2 | Security / privacy | **Raw values leaked to telemetry.** Rejected payloads raised pydantic errors whose text embeds the input (`cvv`, bearer tokens); OpenTelemetry recorded the full traceback on the span. | Card data and secrets in logs, contrary to the project's own gate 15.6. | `record_exception=False` on pipeline and middleware spans; validation errors raised `from None`. | `test_rejected_payload_values_never_reach_telemetry`. |
| 3 | Testing | The existing telemetry-leak test installed a second `TracerProvider`, which OpenTelemetry ignores, so it captured **zero spans** and always passed. | False assurance. | Attach to the real provider; assert spans were captured. | `test_gate15_6_security.py::test_telemetry_no_leakage_exporter`. |
| 4 | Policy logic | A zombie step-up returned early and **skipped risk scoring**: a ₹1.5L payment on an expired card got REVIEW instead of BLOCK. | Zombie detection made high-risk payments easier to push through. | Policy computes the risk decision first; zombie remediation can only make it stricter. | `test_zombie_step_up_never_downgrades_a_risk_block`. |
| 5 | Zombie Card Saver | `REPLACED` cards ignored; first use of a dead credential produced no signal; sustained reuse never escalated to revoke; lifecycle matching was case-sensitive and `str(Enum)` broke on Python 3.12. | The flagship feature missed its core cases. | Dead credential (expired or replaced) → step-up; > 5 reuses in 24 h → high; ≥ 10 → revoke. Lifecycle normalised via `.value`/upper. | 5 new tests in `tests/risk/test_zombie_card_saver.py`. |
| 6 | Zombie enforcement | A REVOKE_TOKEN recommendation was advisory only: the same token kept transacting. | Revocation was not enforced. | Revoked tokens go into a tenant-scoped denylist; next use is CRITICAL / BLOCK. | `test_zombie_revocation_is_enforced_on_next_use`. |
| 7 | Risk logic | Velocity was a stub (`# Normally we would query previous events`), taken from the caller. | An attacker controlled their own velocity signal. | Sliding-window counters over accepted traffic (`backend/realtime/velocity.py`). | `test_observed_velocity_raises_risk_without_caller_hint`. |
| 8 | Webhook flow | A raw PAN request was rejected **after** idempotency registration and risk analysis. | The event id was burned; a corrected retry was refused. | PAN rejected right after schema validation, before any state change. | `test_raw_pan_does_not_consume_event_id`. |
| 9 | Frontend | The browser demo could never pass HMAC: the signer signed Python's JSON (`100.0`) and the browser re-serialised it (`100`). | Every demo scenario returned 401. | Signer returns the exact signed body; client sends it verbatim. | `test_demo_signed_body_verifies_verbatim`; verified live. |
| 10 | Frontend | Risk score read from a non-existent top-level field; zombie and cross-tenant scenarios could not trigger (wrong payload, matching tenant header). | Key features looked broken. | Rewritten against the real response shape; replaced by the live console. | Frontend tests + live browser run. |
| 11 | Gateway flow | Gateway retries of an already-processed event got 401. | Razorpay / YouPI keep retrying for up to an hour. | Duplicates acknowledged with 200 `duplicate`, not reprocessed. | Razorpay and YouPI duplicate tests. |
| 12 | Performance | Every audit read re-hashed the whole ledger; the summary loaded every row; in-memory idempotency grew without bound; Redis client reconnected per request. | Degrades linearly with traffic (≈170k rows/day under live load). | Incremental chain verification on reads, full check at `GET /audit/verify`; SQL aggregation; bounded store; cached client. | `test_incremental_verification_detects_tampering_of_new_rows`. |
| 13 | Legacy service | `execute_token_remediation` revoked tokens with no policy check and a hard-coded risk score of 86 (open PR #1). | Unauthorised revocations. | Applied PR #1 (PolicyEngine gate, fail-closed on exceptions). | `backend/tests/test_zombie_card_saver.py`. |
| 14 | CI | 441 Ruff errors in new code (CI lint gate would fail); release guard required deleted components. | Red pipeline. | Lint clean; release guard lists the files that exist. | `ruff check backend scripts`, `release_guard.py`. |
| 15 | Deploy | Dockerfile launched the legacy `app.main`, not the Netvrio API the frontend talks to; CORS was `*` with credentials in test. | The container served the wrong backend. | Docker runs `backend.api.app` and serves the built SPA; CORS uses explicit origins, no credentials. | Live run on :8000. |

## New capabilities (security reviewed)

- **Threat intelligence** (`backend/threat_intel/`): local indicator store, so no per-payment calls and no customer data sent to third parties. Feeds (Tor exit list, Spamhaus DROP) are opt-in, HTTPS-only, size-capped and strictly parsed (non-global and over-broad ranges dropped), and fail static on errors. Matches are evidence only.
- **Card exposure monitoring** (OnionClaw): `scripts/onionclaw_exposure_adapter.py` runs on an isolated collector, turns leaked card numbers into the existing keyed fingerprint and discards them. Netvrio receives signed fingerprints only (`POST /intel/exposures`), revokes linked tokens at once and blocks exposed cards inline. OnionClaw itself is not embedded: it needs Tor, and automated dark-web access needs legal sign-off.
- **YouPI-PG UPI adapter**: V1 and timestamp-bound V2 signatures, delivery-id de-duplication, unreconciled payments flagged. The project is experimental and not NPCI or bank approved; observed success is not settlement.
- **Analyst resolutions**: Approve / Decline on REVIEW decisions, written to the hash chain once, broadcast live.

## Verification

| Gate | Result |
|---|---|
| Backend tests | 316 passed, 1 skipped (live Razorpay order test needs real keys) |
| Coverage gate (`backend/app`, ≥ 75%) | 81% |
| Ruff (`backend/ scripts/`) | clean |
| Release guard, frozen test-set hash | pass |
| Frontend | `tsc` strict, 22 Vitest tests, production build |
| Smoke test against running API | 8/8 |
| Live browser | stream, review approve, exposure drill (40 fingerprints, linked tokens revoked and blocked), YouPI webhook + duplicate, command palette, 375px layout |

## Not verified / known limits

Production authentication is not connected. The event bus, behaviour windows and indicator store are in-process (single worker; Redis would be needed to scale out). SQLite audit store. Live AI providers, live threat-feed downloads and real Razorpay/YouPI deliveries were not exercised against the real services from this environment.
