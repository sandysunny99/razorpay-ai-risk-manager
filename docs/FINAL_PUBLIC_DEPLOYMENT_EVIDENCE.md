# Final Public Deployment Evidence Record (v2.0.0-rc1)

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Commit**: `915c2f2`  
**Timestamp**: 2026-08-23T17:11:00+05:30  
**Submission Readiness**: **READY_FOR_SUBMISSION**  

---

## 1. Verified Evidence & Capability Table

| Subsystem / Capability | Environment State | Implementation Reference | Empirical Evidence | Status | Allowed Submission Claim |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GitHub Repository** | **DEPLOYMENT_CONFIGURED** | `razorpay-ai-risk-manager` | `.github/workflows/ci.yml` | **VALIDATED** | *"GitHub CI automated quality gate pipeline"* |
| **Render Web Service** | **DEPLOYMENT_CONFIGURED** | `render.yaml` + `Dockerfile` | Multi-stage Docker config | **VALIDATED** | *"Render Docker Web Service configuration"* |
| **Cloudflare Edge** | **SIMULATED** | `CloudflareAdapter` | `verify_cloudflare_security.py` | **VALIDATED** | *"Cloudflare-compatible edge telemetry adapter"* |
| **Razorpay Vault Gateway** | **TEST_MODE / MOCK** | `RazorpayTestAdapter` | `test_e2e_agent.py` | **VALIDATED** | *"Razorpay Test Mode token management adapter"* |
| **Threat Intelligence** | **SYNTHETIC / OFFLINE** | `SyntheticThreatIntelProvider`| `test_risk_engines.py` | **VALIDATED** | *"Deterministic synthetic threat intelligence"* |
| **Backend Test Suite** | **LOCAL** | 12 Test Modules | `pytest -q` (54/54 PASS) | **VALIDATED** | *"100% automated test pass rate"* |
| **Held-Out Test Set** | **LOCAL (Frozen $N=300$)** | `evaluation/test.jsonl` | `run_final_evaluation.py` | **VALIDATED** | *"Measured Result on Frozen Held-Out Test Set"* |
| **Data Protection Core** | **LOCAL** | `AES-256-GCM`, `KMS`, `DLP` | `verify_data_security.py` | **VALIDATED** | *"Authenticated encryption and DLP Luhn scanner"* |
| **SOC Web Application** | **LOCAL** | React 18 + Vite | `npm run build` (1,816 modules) | **VALIDATED** | *"14-view React operations dashboard with 0 errors"* |
| **Deterministic Demo** | **LOCAL** | 10 Scenarios + Reset | `scripts/reset_demo.py` | **VALIDATED** | *"10 deterministic demonstration workflows"* |
