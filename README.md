# Netvrio
Real-time AI payment risk & security console.

Every payment event — synthetic traffic or a real **Razorpay test-mode webhook** — streams through one
protected pipeline and lands on a live operations dashboard within milliseconds:

```
Ingress security ─────────────────────────────►  Analysis ─────────────────────►  Decision
HMAC → strict schema → tenant binding →          Deterministic risk               Deterministic policy engine
raw-PAN guard → replay window → idempotency      (observed velocity) →            → SHA-256 hash-chained audit
                                                 Zombie Card Saver →              → live SSE stream
                                                 AI advisory (advisory only)
```

## What you see

| Page | What it does |
|---|---|
| **Live operations** (`/`) | Review queue with working Approve / Decline (hash-chained), live SSE event stream with filters and a per-event pipeline trace, status strip, and charts that each answer one question. |
| **Threat intelligence** (`/threats`) | Indicator sources and their health, learned revocations, card exposure reports, recent matches. |
| **Audit ledger** (`/ledger`) | Tenant-isolated, metadata-only records, analyst resolutions, incremental and full hash-chain verification. |
| **Integrations** (`/integrations`) | Razorpay and YouPI-PG webhook setup and delivery counters, synthetic traffic controls, AI provider health, measured platform status. |

Press **Ctrl/⌘K** anywhere for the command palette (navigate, open an audit ID, verify the ledger, refresh feeds, start/stop traffic).
Design direction and the anti-slop delivery gate: [DESIGN.md](DESIGN.md). Full audit: [docs/AUDIT_REPORT.md](docs/AUDIT_REPORT.md).

## Key capabilities
1. **One pipeline for everything** — `run_pipeline()` in `backend/api/routes/webhooks.py` is used by the webhook API, the live generator and the Razorpay adapter.
2. **Real-time stream** — in-process, tenant-scoped event bus (`backend/realtime/bus.py`) pushed to the browser over SSE (`GET /live/events`).
3. **Observed behaviour** — customer velocity and dead-token reuse are computed from accepted traffic with sliding windows (`backend/realtime/velocity.py`), not taken on trust from the caller.
4. **Zombie Card Saver** — detects reuse of expired/replaced or compromised credentials and recommends step-up or revocation; token revocation in the legacy service is gated by the PolicyEngine (R-001).
5. **Razorpay adapter** — verifies `X-Razorpay-Signature`, drops card details/e-mail/phone, pseudonymizes customers, converts paise → rupees, de-duplicates retries by event id.
6. **AI advisory with deterministic authority** — LLM output must cite trusted evidence IDs and can never override the policy engine; with no provider configured the pipeline fails safe.
7. **Tamper-evident audit** — every decision and analyst resolution is appended to a SHA-256 hash chain (incremental check on reads, full re-hash on demand).
8. **Threat intelligence** — local indicator store (synthetic seed, opt-in Tor exit list and Spamhaus DROP), safe parsing, fail-static refresh; revocations learned from Zombie Card Saver are enforced on the next use.
9. **Card exposure monitoring** — an isolated [OnionClaw](https://github.com/jacobjandon/onionclaw) collector plus `scripts/onionclaw_exposure_adapter.py` reports leaked cards as keyed fingerprints only; Netvrio revokes linked tokens and blocks exposed cards.
10. **YouPI-PG (UPI)** — adapter for the self-hosted [YouPI-PG](https://github.com/youpi-pg/YouPI-PG) gateway (experimental, not NPCI/bank approved): V1/V2 signatures, delivery-id de-duplication, unreconciled payments flagged.
11. **ML second opinion** — LightGBM with per-decision TreeSHAP reasons. Layered as rules first, model second: the model can only send an otherwise allowed payment to human review. Trained on a scenario simulator (`python -m backend.ml.train`); the model card in `backend/ml/model/` records metrics and why the bundled evaluation set is not used for training.
12. **PII masking** — [Presidio](https://github.com/data-privacy-stack/presidio) masks cards, UPI IDs, Indian mobile numbers, Aadhaar, PAN, e-mail and IPs in customer free text before evidence, audit, the stream or any LLM; regex fallback when Presidio is not installed (`backend/requirements-privacy.txt`).
13. **Abuse and supply-chain controls** — per-client rate limits on ingest endpoints; Bandit, pip-audit and Gitleaks in CI. WAF, CrowdSec and OpenBao guidance: [docs/EDGE_SECURITY.md](docs/EDGE_SECURITY.md).

## Run it

```bash
pip install -r backend/requirements.txt
```

```bash
cd frontend && npm install && npm run build && cd ..
```

Start the API (it also serves the built dashboard on http://localhost:8000). PowerShell:

```powershell
$env:NETVRIO_ENV="test"; $env:NETVRIO_DEMO_MODE="true"; $env:NETVRIO_LIVE_AUTOSTART="true"; $env:OTEL_EXPORTER_MODE="none"
python -m uvicorn backend.api.app:app --port 8000
```

bash:

```bash
NETVRIO_ENV=test NETVRIO_DEMO_MODE=true NETVRIO_LIVE_AUTOSTART=true OTEL_EXPORTER_MODE=none python -m uvicorn backend.api.app:app --port 8000
```

For frontend hot reload run `npm run dev` in `frontend/` (http://localhost:5173 talks to the API on :8000).

Or with Docker (single container, live traffic on by default):

```bash
docker compose up --build
```

### Connect Razorpay (test mode)
1. Set `RAZORPAY_WEBHOOK_SECRET` (and optionally `RAZORPAY_TENANT_ID`, default `tenant_123`).
2. Razorpay Dashboard → Test Mode → Settings → Webhooks → add `https://<your-host>/integrations/razorpay/webhook`
   (use a tunnel such as ngrok or cloudflared for localhost) with the same secret.
3. Subscribe to `payment.authorized`, `payment.captured`, `payment.failed` and make a test payment — it appears on Live Operations instantly.

### Card exposure monitoring (OnionClaw)
Run OnionClaw on a separate, legally approved collector host (it needs Tor). Then:

```bash
FINGERPRINT_HMAC_SECRET=<hex> EXPOSURE_FEED_SECRET=<secret> python scripts/onionclaw_exposure_adapter.py onionclaw_results.json --post https://<api>/intel/exposures
```

Card numbers never leave the adapter. To rehearse against a running demo API: `python scripts/demo_exposure_drill.py` (same two secrets).

### Connect YouPI-PG (UPI): the primary payment source
Set `YOUPI_WEBHOOK_SECRET` (optionally `YOUPI_REQUIRE_V2=true`, `YOUPI_TENANT_ID`) and point the YouPI merchant webhook at `/integrations/youpi/webhook`.

### Configuration

| Variable | Purpose |
|---|---|
| `NETVRIO_ENV` | `test` enables the demo tenant header (`x-tenant-id`). **Unset means production** (fail closed): header auth and the dummy webhook secret are refused. |
| `NETVRIO_DEMO_MODE` | `true` enables the synthetic traffic generator and demo signer. |
| `NETVRIO_LIVE_AUTOSTART` | `true` starts synthetic traffic at boot. |
| `WEBHOOK_SECRET` | Internal webhook HMAC secret (a dummy is used only when `NETVRIO_ENV=test`). |
| `RAZORPAY_WEBHOOK_SECRET` / `RAZORPAY_TENANT_ID` | Razorpay adapter. |
| `YOUPI_WEBHOOK_SECRET` / `YOUPI_REQUIRE_V2` / `YOUPI_TENANT_ID` | YouPI-PG adapter. |
| `EXPOSURE_FEED_SECRET` / `FINGERPRINT_HMAC_SECRET` | Card exposure ingestion and the shared card-fingerprint key. |
| `NETVRIO_LLM_CHAIN` / `NETVRIO_LLM_SCOPE` / `NETVRIO_LLM_MAX_PER_MIN` | AI provider order (Groq, Cloudflare, Gemini, NVIDIA, Hugging Face, Grok), which payments get an AI note (`flagged` or `all`) and the per-minute call budget. Keys: `GROQ_API_KEY`, `CLOUDFLARE_ACCOUNT_ID`/`CLOUDFLARE_API_TOKEN`, `GEMINI_API_KEY`, `NVIDIA_API_KEY`, `HF_API_KEY`/`HF_TOKEN`, `GROK_API_KEY`. |
| `ABUSE_CH_AUTH_KEY` / `OTX_API_KEY` | abuse.ch ThreatFox and AlienVault OTX feeds (Feodo Tracker, Spamhaus DROP and Tor need no key). |
| `NETVRIO_ML_ESCALATE` / `NETVRIO_ML_THRESHOLD` | Let the model send ALLOW decisions to review (off by default; on in Docker demo) and the score threshold (0.8). |
| `NETVRIO_PII_ENGINE` | `auto` (Presidio if installed), `presidio` or `regex`. |
| `NETVRIO_RATE_LIMIT` / `RATE_LIMIT_STORAGE_URI` | Ingest rate limit per client (default `300/minute`) and its storage (`memory://` or `redis://...`). |
| `NETVRIO_TI_LIVE_FEEDS` / `NETVRIO_TI_REFRESH_S` | Download Tor exit / Spamhaus DROP lists (off by default) and refresh interval. |
| `AUDIT_DB_URL` | Audit ledger database (default `sqlite:///netvrio_audit.db`). |
| `CORS_ALLOWED_ORIGINS` | Comma-separated; defaults to Vite dev origins outside production. |
| `OTEL_EXPORTER_MODE` | `console` (default) prints spans; `none` silences them. |

## API

| Endpoint | |
|---|---|
| `POST /webhooks/payment` | Signed (`x-signature`) payment event → decision |
| `POST /integrations/razorpay/webhook` | Razorpay webhook (`X-Razorpay-Signature`) |
| `POST /integrations/youpi/webhook` | YouPI-PG webhook (`X-Gateway-Signature`, `-V2`) |
| `POST /intel/exposures` · `GET /intel/exposures` | Signed card-exposure fingerprints · summary |
| `GET /intel/status` · `GET /intel/matches` · `POST /intel/refresh` | Threat-intel sources, matches, feed refresh (demo mode) |
| `POST /audit/{id}/resolution` · `GET /audit/verify` | Analyst Approve/Decline of a REVIEW · full chain re-hash |
| `GET /live/events?tenant=` | SSE stream of decisions/rejections |
| `GET /live/snapshot` · `GET/POST /live/generator` | Recent events · synthetic traffic control (demo mode) |
| `GET /audit` · `GET /audit/summary` · `GET /audit/{id}` | Tenant-scoped audit metadata |
| `GET /health` · `GET /health/providers` · `GET /integrations/razorpay/status` | Health |

## Tests

```bash
python -m pytest backend/tests -q
```

```bash
cd frontend && npx vitest run
```

* **Backend:** 369 passed / 1 skipped (live Razorpay order test needs real keys); coverage gate 81%
* **Supply chain:** pip-audit no known vulnerabilities; Bandit 0 medium+ findings
* **Frontend:** 24 passed; `tsc` strict + production build pass
* **Smoke test:** `python scripts/demo_smoke_test.py` against a running API — 8/8

## Limitations
This is a prototype. Production authentication is **not connected** (demo tenant header only), the event bus and
behavioural windows are in-process (single worker), the audit ledger uses SQLite, and live AI providers are
**not verified**. Synthetic traffic and Razorpay test mode only — no real cardholder data.
