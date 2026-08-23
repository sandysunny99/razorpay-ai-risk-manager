# Render Cloud Deployment Specification

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Infrastructure Blueprint**: `render.yaml`  
**Runtime**: Docker Multi-Stage (`Dockerfile`)  
**Deployment Status**: **DEPLOYMENT_CONFIGURED & DOCKER_VALIDATED**  

---

## 1. Render Blueprint Configuration (`render.yaml`)

```yaml
services:
  - type: web
    name: razorpay-risk-manager
    env: docker
    dockerfilePath: ./Dockerfile
    plan: standard
    healthCheckPath: /health
    envVars:
      - key: PORT
        value: 8000
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        value: sqlite:////app/risk_management.db
      - key: SECRET_KEY
        generateValue: true
      - key: JWT_SECRET
        generateValue: true
      - key: HMAC_KEY
        generateValue: true
      - key: ENCRYPTION_KEY
        generateValue: true
```

---

## 2. Liveness Probes & Readiness Checkpoints

- **Liveness Probe**: `GET /health` $\rightarrow$ `{"status":"healthy","service":"Razorpay AI Risk Manager Gateway","version":"2.0.0-rc1"}`
- **Dependency Health**: `GET /api/v1/health/dependencies` $\rightarrow$ `{"status":"healthy","dependencies":{"sqlite_database":"UP",...}}`
- **Frontend Assets**: Statically served via FastAPI from compiled Vite distribution `/app/frontend/dist`.
