# Final Release Truth Matrix (v2.0.0-rc1)

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Commit**: `73d4a9a`  
**Date**: August 23, 2026  
**Status**: **ALL CLAIMS RESTRICTED TO STRICTLY VERIFIED ARTIFACTS**  

---

## 1. Subsystem Capability Truth & Allowed Claims Matrix

| Capability / Subsystem | Implementation Type | Operational Mode | Execution Evidence Source | Verification Status | Allowed Claim in Submission |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Deterministic Risk Engine** | 6-Factor Python Kernel | REAL / DETERMINISTIC | `scripts/run_final_evaluation.py` | **VERIFIED** | *"Deterministic mathematical payment risk scoring (0-100 scale)"* |
| **Policy Guardrail Engine** | 5-Tier Boundary Rules | REAL / DETERMINISTIC | `backend/tests/test_policy.py` | **VERIFIED** | *"Centralized policy guardrail engine with T=40 detection & T=75 remediation"* |
| **Cloudflare Edge Perimeter**| Python Normalization Adapter | **SIMULATED** | `scripts/verify_cloudflare_security.py`| **ADAPTER_VALIDATED** | *"Cloudflare-compatible security telemetry adapter with 1-99 bot taxonomy"* |
| **Razorpay Gateway Vault** | Gateway Adapter | **TEST_MODE / MOCK** | `backend/tests/test_e2e_agent.py` | **MOCK_VALIDATED** | *"Razorpay Test/Mock adapter simulating token actions and Step-Up 2FA"* |
| **Threat Intelligence** | Synthetic Breach Provider | **SYNTHETIC / OFFLINE**| `backend/tests/test_risk_engines.py` | **SYNTHETIC_VALIDATED** | *"Synthetic threat intelligence simulating stealer dumps for offline evaluation"* |
| **AES-256-GCM Encryption** | NIST-Standard GCM Cipher | REAL / LOCAL | `scripts/verify_data_security.py` | **LOCAL_VALIDATED** | *"AES-256-GCM authenticated field encryption with 96-bit unique nonces"* |
| **Key Provider & Rotation** | Versioned KMS Provider | REAL / LOCAL | `scripts/verify_data_security.py` | **LOCAL_VALIDATED** | *"Versioned key provider supporting rotation with zero raw key leakage"* |
| **Data Loss Prevention (DLP)**| Regex & Luhn Scrubber | REAL / LOCAL | `scripts/verify_data_security.py` | **LOCAL_VALIDATED** | *"Multi-pattern DLP with Luhn PAN candidate scrubber & secret scanner"* |
| **Dynamic Server Masking** | REST API Serializers | REAL / LOCAL | `backend/tests/test_webapp_security.py`| **LOCAL_VALIDATED** | *"Role-aware server-side masking across all sensitive entity fields"* |
| **Multi-Tenant Isolation** | SQLite Merchant Scoping | REAL / LOCAL | `backend/tests/test_multi_tenancy.py` | **LOCAL_VALIDATED** | *"Multi-tenant IDOR protection verified across merchant boundaries (4 tests)"* |
| **Cryptographic Audit Log** | SHA-256 Hash Chain Ledger | REAL / LOCAL | `backend/tests/test_audit_chain.py` | **LOCAL_VALIDATED** | *"SHA-256 tamper-evident hash-chained audit ledger with 0 tampered blocks"* |
| **Container & Cloud Deploy** | Dockerfile + Compose + Render | REAL / LOCAL & CONFIG | `Dockerfile`, `render.yaml` | **DEPLOYMENT_CONFIGURED** | *"Production-ready multi-stage Docker build & Render cloud blueprint"* |
| **Held-Out Test Baseline** | 300 Frozen Records ($N=300$) | IMMUTABLE BENCHMARK | `scripts/verify_test_set.py` | **VERIFIED** | *"Measured results on frozen held-out test set: 88.06% Rec (T=40), 100% Prec (T=75)"* |
| **Interactive SOC Dashboard** | React 18 + Vite + Tailwind | REAL / LOCAL | `frontend/dist/` (1,816 modules) | **LOCAL_VALIDATED** | *"14-view React SOC dashboard with live interactive DLP sandbox"* |
