# GitHub Repository & CI Pipeline Specification

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Commit**: `4609405`  
**Repository Name**: `razorpay-ai-risk-manager`  
**Visibility**: `PUBLIC (Configured for Hackathon Submission)`  
**CI Configuration**: `.github/workflows/ci.yml` (Automated 8-stage quality pipeline)  
**Repository State**: **DEPLOYMENT_CONFIGURED & READY_FOR_PUSH**  

---

## 1. Automated CI Pipeline Stages (`.github/workflows/ci.yml`)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Test Set Hash Immutability Gate (SHA-256 Checksum)       │
├─────────────────────────────────────────────────────────────┤
│ 2. Automated Backend Pytest Suite (54 / 54 Tests)           │
├─────────────────────────────────────────────────────────────┤
│ 3. Reproducible Final Evaluation Benchmark (N = 300)        │
├─────────────────────────────────────────────────────────────┤
│ 4. Release Guard Policy & Dataset Isolation Verification    │
├─────────────────────────────────────────────────────────────┤
│ 5. Cloudflare Security Telemetry & Bot Classification Gate │
├─────────────────────────────────────────────────────────────┤
│ 6. Data Security, AES-256-GCM & DLP Scanner Gate            │
├─────────────────────────────────────────────────────────────┤
│ 7. Frontend Production Bundle Build (React 18 + Vite)       │
├─────────────────────────────────────────────────────────────┤
│ 8. Docker Multi-Stage Image Build Verification              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Remote Configuration Instructions

```bash
# Add public remote origin and push main branch
git remote add origin https://github.com/<user>/razorpay-ai-risk-manager.git
git branch -M main
git push -u origin main
git push origin v2.0.0-rc1
```
