# CI Pipeline Failure Investigation & Root Cause Analysis

**Repository**: `sandysunny99/razorpay-ai-risk-manager`  
**Failing Commit**: `5bfbaac`  
**Corrected Commit**: `8666eb4`  
**Release Candidate**: `v2.0.0-rc2`  

---

## 1. Executive Summary

During the integration of the **Zombie Card Saver** module and **Real-Time Telemetry Enrichment**, the GitHub Actions automated CI workflow failed. A systematic audit was conducted across all 14 pipeline steps to identify the root cause without masking underlying issues.

---

## 2. Root Cause Audit & Identified Defects

### Defect 1: Docker Multi-Stage Build Peer Dependency Resolution (Step 8)
- **Symptom**: In the Docker build stage (`FROM node:20-alpine AS frontend-builder`), `RUN npm install --no-audit` failed with npm 10 `ERESOLVE` due to peer dependency resolution between `lucide-react` and React 18 in fresh container environments.
- **Root Cause**: The container build lacked `--legacy-peer-deps` flag present in the CI host step.
- **Fix**: Updated `Dockerfile` line 8:
  ```dockerfile
  RUN npm install --no-audit --legacy-peer-deps
  ```

### Defect 2: Python Setup Dependency Cache Path in CI Workflow (Step 3)
- **Symptom**: `actions/setup-python@v5` with `cache: 'pip'` was failing to locate the root dependency file because `requirements.txt` was located in `backend/requirements.txt`.
- **Root Cause**: Missing `cache-dependency-path: backend/requirements.txt` in `.github/workflows/ci.yml`.
- **Fix**: Explicitly configured `cache-dependency-path: backend/requirements.txt` and created a standard root `requirements.txt` redirect.

### Defect 3: Hardcoded Localhost in Frontend API Base (Step 7)
- **Symptom**: `frontend/src/services/api.ts` hardcoded `http://localhost:8000/api/v1`, creating an anti-pattern for production builds.
- **Root Cause**: Direct string constant instead of environment-aware / relative routing.
- **Fix**: Replaced with `import.meta.env.VITE_API_BASE_URL || '/api/v1'` and configured dev-server proxy in `vite.config.ts`.

### Defect 4: Stale Hardcoded Test Count in CI Labels
- **Symptom**: `.github/workflows/ci.yml` and `scripts/pre_deploy.py` had static label `Automated Backend Pytest Suite (54 Tests)` while the test suite had grown to 63 tests.
- **Fix**: Updated label to `Automated Backend Pytest Suite` to reflect dynamic pytest test discovery.

---

## 3. Files Modified for CI Hardening

| File | Modification Summary |
| :--- | :--- |
| [`.github/workflows/ci.yml`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/.github/workflows/ci.yml) | Added `cache-dependency-path`, environment defaults, and updated test suite label. |
| [`Dockerfile`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/Dockerfile) | Added `--legacy-peer-deps` to frontend builder stage. |
| [`backend/app/main.py`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/backend/app/main.py) | Mounted production SPA static assets and updated API version to `2.0.0-rc2`. |
| [`frontend/src/services/api.ts`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/frontend/src/services/api.ts) | Environment-aware `API_BASE` resolution (`/api/v1`). |
| [`frontend/vite.config.ts`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/frontend/vite.config.ts) | Added development server proxy for `/api`. |
| [`frontend/src/components/Header.tsx`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/frontend/src/components/Header.tsx) | Updated release badge to `v2.0.0-rc2`. |
| [`requirements.txt`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/requirements.txt) | Root requirements pointer. |
| [`scripts/pre_deploy.py`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/scripts/pre_deploy.py) | Standardized test discovery label. |
