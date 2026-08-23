# Final Deployment Evidence & Verification Specification

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Commit**: `4a80238`  
**Deployment Platform**: Render Docker Blueprint (`render.yaml`) & Multi-Stage `Dockerfile`  
**Edge Protection**: Cloudflare Perimeter (WAF, Bot Management, Rate Limiting, Turnstile, Ray ID Tracing)  
**Deployment Lifecycle Status**: **DEPLOYMENT_CONFIGURED & LOCAL/DOCKER VALIDATED**  

---

## 1. Subsystem Health & Status Matrix

| Subsystem / Service | Operational Mode | Health Probe & Status | Evidence Source |
| :--- | :--- | :--- | :--- |
| **FastAPI Security Gateway** | **ACTIVE** | `GET /health` $\rightarrow$ `{"status":"healthy"}` | Verified via `scripts/pre_deploy.py` |
| **Dependency Probes** | **UP** | `GET /api/v1/health/dependencies` $\rightarrow$ `UP` | Verified via test suite |
| **SQLite / SQLAlchemy DB** | **ACTIVE** | `risk_management.db` seeded & scoped | Verified via `scripts/reset_demo.py` |
| **Cloudflare Edge Adapter** | **SIMULATED / TEST** | `CloudflareAdapter` normalizes WAF/Bot signals | Verified via `verify_cloudflare_security.py` |
| **Razorpay Vault Adapter** | **TEST_MODE / MOCK** | `RazorpayTestAdapter` token revocation | Verified via `test_e2e_agent.py` |
| **Threat Intel Provider** | **SYNTHETIC** | `SyntheticThreatIntelProvider` stealer logs | Verified via `test_risk_engines.py` |
| **React 18 Dashboard** | **ACTIVE** | 1,816 modules compiled with 0 errors | Verified via `npm run build` (1.15s) |

---

## 2. Post-Deployment Verification Checkpoints

1. **Liveness Probe**:
   - `curl -f http://localhost:8000/health` $\rightarrow$ `{"status":"healthy","service":"Razorpay AI Risk Manager Gateway","version":"2.0.0-rc1"}`
2. **Data Protection Matrix**:
   - `curl -f http://localhost:8000/api/v1/security/data-protection` $\rightarrow$ Asserts AES-256-GCM field encryption, HMAC fingerprinting, and dynamic masking.
3. **Interactive DLP Test**:
   - `curl -X POST http://localhost:8000/api/v1/security/dlp/test -H "Content-Type: application/json" -d '{"input_text":"Testing card 4111 1111 1111 1111"}'` $\rightarrow$ Returns sanitized masked output `**** **** **** 1111`.
4. **Golden Demo Workflow**:
   - Stealer dump + Zombie token scenario runs end-to-end, enforces Policy `PR-01`, revokes active vault token, drops risk $94 \rightarrow 16$, and creates a verifiable SHA-256 audit block.
