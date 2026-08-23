# Deployment Evidence & Verification Record

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Version**: `v2.0.0-rc1`  
**Commit**: `8bc6e8f`  
**Deployment Blueprint**: `render.yaml` & Multi-Stage `Dockerfile`  
**Status**: **DEPLOYMENT_CONFIGURED & LOCAL/DOCKER VALIDATED**  

---

## 1. Container & Deployment Pipeline Architecture

```
                 INTERNET / SOC ANALYST
                           │
                           ▼
             ┌───────────────────────────┐
             │ CLOUDFLARE EDGE PERIMETER │
             │ • DDoS / WAF / Turnstile  │
             │ • Strict TLS 1.3 + HSTS   │
             └─────────────┬─────────────┘
                           │ HTTPS Origin Proxy
                           ▼
             ┌───────────────────────────┐
             │    RENDER / WEB SERVICE   │
             │ • Port 8000 (FastAPI)     │
             │ • Static React UI (dist)  │
             │ • Health Check: /health   │
             └─────────────┬─────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌──────────────────┐               ┌──────────────────┐
│ FASTAPI GATEWAY  │               │ REACT 18 DASHBD  │
│ 10 REST Routers  │               │ SOC & Evaluation │
└──────────────────┘               └──────────────────┘
```

---

## 2. Environment Configuration & Secrets Management

| Configuration Key | Runtime Target | Production Source | Public / Client Leaked? |
| :--- | :--- | :--- | :--- |
| `APP_MODE` | Origin Server | `demo` / `production-like` | **NO** |
| `DRY_RUN` | Origin Server | `true` | **NO** |
| `HMAC_SECRET_KEY` | Origin Server | Server Environment / KMS | **NO** (Zero Client Leakage) |
| `MASTER_ENCRYPTION_KEY` | Origin Server | AES-256 Secret (KMS) | **NO** (Zero Client Leakage) |
| `DATABASE_URL` | Origin Server | `sqlite:///./risk_management.db` | **NO** (Local volume / secure DB) |
| `VITE_API_BASE_URL` | Frontend Client | `/api/v1` (Relative or Origin HTTPS) | **SAFE** (Public API Route) |

---

## 3. Post-Deployment Smoke Test Checkpoints

| Endpoint / Action | Expected Result | Verified Evidence |
| :--- | :--- | :--- |
| `GET /health` | HTTP 200 `{"status":"healthy"}` | Verified via `scripts/pre_deploy.py` |
| `GET /api/v1/health/dependencies` | HTTP 200 `{"dependencies":{"sqlite_database":"UP", ...}}` | Verified via test suite |
| `GET /api/v1/security/data-protection`| HTTP 200 Data at Rest & In Transit status | Verified via test suite |
| `POST /api/v1/security/dlp/test` | HTTP 200 Real-time Luhn PAN redaction | Verified via test suite |
| `GET /api/v1/exposure/statistics` | HTTP 200 CTI monitored vs exposed cards | Verified via test suite |
| `POST /api/v1/agent/scenarios/reset` | HTTP 200 Demo state reset | Verified via `scripts/reset_demo.py` |
