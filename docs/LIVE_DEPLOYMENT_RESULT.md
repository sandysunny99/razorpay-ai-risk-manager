# Live Deployment Result & Public Service Specification

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Commit**: `f4445f3`  
**Deployment Target**: Render Web Service (`render.yaml`)  
**Container Blueprint**: Multi-Stage Dockerfile (`python:3.12-slim` + `node:20-alpine`)  
**Deployment Lifecycle Status**: **DEPLOYMENT_CONFIGURED & LOCAL/DOCKER VALIDATED**  

---

## 1. Public Service Architecture & Endpoints

- **Service Name**: `razorpay-risk-manager`
- **Port**: `8000` (FastAPI / Uvicorn)
- **Health Check Probe**: `/health` (Interval: 30s, Timeout: 5s, Retries: 3)
- **API Base Route**: `/api/v1`
- **Frontend Assets**: Statically bundled via Vite (`dist/index.html`)

---

## 2. Live Health & Dependency Verification Results

| Endpoint Path | Method | Expected Response | Verified Status |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | HTML / API Welcome | **PASS** |
| `/health` | `GET` | `{"status":"healthy","service":"Razorpay AI Risk Manager Gateway"}` | **HEALTHY** |
| `/api/v1/health/dependencies` | `GET` | `{"status":"healthy","dependencies":{"sqlite_database":"UP", ...}}` | **HEALTHY** |
| `/api/v1/security/data-protection`| `GET` | AES-256-GCM & In-Transit TLS Status | **PASS** |
| `/api/v1/security/dlp/test` | `POST` | Real-time Luhn PAN Redaction | **PASS** |
| `/api/v1/exposure/statistics` | `GET` | Monitored vs Exposed Card Counts | **PASS** |
| `/api/v1/agent/scenarios/reset` | `POST` | 1-Click Demo State Reset | **PASS** |
