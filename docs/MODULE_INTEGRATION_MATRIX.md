# Module Integration Matrix (v2.0.0-rc1)

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Baseline Commit**: `915c2f2`  
**Status**: **ALL MODULES FULLY INTEGRATED & VALIDATED**  

---

## 1. Full Module Inventory & Integration Table

| Module | Backend Source | Frontend Consumer | API Endpoint | Database Model | Dependencies | Current Status | Integration Status | Test Suite | UI Location | Deployment Requirement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Deterministic Risk Engine** | `backend/app/engines/risk_scorer.py` | `TransactionInvestigation.tsx`, `RiskDistribution.tsx` | `/api/v1/transactions/{id}/assess` | `Transaction`, `RiskAssessment` | None | **READY** | **INTEGRATED** | `test_risk_engines.py` | `/transactions/:id`, `/dashboard` | Standard Python runtime |
| **Policy Guardrail Engine** | `backend/app/engines/policy_engine.py` | `PolicyDecisionCard.tsx`, `ResponseTiers.tsx` | `/api/v1/policy/evaluate` | `PolicyRule`, `PolicyExecution` | `risk_scorer` | **READY** | **INTEGRATED** | `test_tiered_response.py` | `/transactions/:id`, `/actions` | Zero-dependency rules kernel |
| **Dynamic Risk Agent** | `backend/app/agent/risk_agent.py` | `AgentInvestigationTimeline.tsx` | `/api/v1/agent/investigate` | `AgentSession`, `ToolExecution` | `risk_scorer`, `policy_engine` | **READY** | **INTEGRATED** | `test_e2e_agent.py` | `/agent`, `/transactions/:id` | Tool calling & attribution |
| **Cloudflare Edge Adapter** | `backend/app/integrations/cloudflare_adapter.py` | `CloudflareSecurityView.tsx`, `Header.tsx` | `/api/v1/integrations/cloudflare/telemetry` | `EdgeSecurityEvent` | None | **SIMULATED** | **INTEGRATED** | `verify_cloudflare_security.py` | `/security`, `/transactions/:id` | Header normalization |
| **Razorpay Vault Adapter** | `backend/app/integrations/razorpay_adapter.py` | `TokenIntelligenceView.tsx`, `ActionsView.tsx` | `/api/v1/tokens/{id}/revoke`, `/step-up` | `PaymentToken`, `TokenAction` | None | **TEST_MODE / MOCK**| **INTEGRATED** | `test_webapp_security.py` | `/tokens`, `/actions` | Signature & webhook validation |
| **Threat Intelligence Core** | `backend/app/integrations/threat_intel.py` | `ThreatIntelligenceView.tsx` | `/api/v1/threat-intelligence/matches` | `ThreatMatchRecord` | None | **SYNTHETIC** | **INTEGRATED** | `test_risk_engines.py` | `/threat-intelligence` | Deterministic offline feeds |
| **AES-256-GCM Encryption** | `backend/app/security/encryption.py` | `DataProtectionView.tsx` | `/api/v1/security/data-protection` | SQLite Encrypted Fields | `cryptography` | **READY** | **INTEGRATED** | `verify_data_security.py` | `/security/data-protection` | NIST 96-bit unique nonces |
| **KMS Key Provider** | `backend/app/security/key_provider.py` | `SecurityCenter.tsx` | `/api/v1/security/keys/status` | `KeyMetadata` | None | **READY** | **INTEGRATED** | `verify_data_security.py` | `/security` | Versioned key rotation |
| **DLP Luhn Scrubber** | `backend/app/security/masking.py` | `DlpSandbox.tsx` | `/api/v1/security/dlp/test` | None (In-Memory Scrubber) | None | **READY** | **INTEGRATED** | `verify_data_security.py` | `/security`, `/security/data-protection` | Real-time Luhn sanitizer |
| **SHA-256 Audit Ledger** | `backend/app/audit/audit_ledger.py` | `AuditLedgerView.tsx` | `/api/v1/audit`, `/api/v1/audit/verify` | `AuditBlock` | `hashlib` | **READY** | **INTEGRATED** | `test_audit_chain.py` | `/audit` | Tamper-evident hash chain |
| **Multi-Tenant Isolation** | `backend/app/db/` | All Views | All `/api/v1/*` routes | All Models (`merchant_id`) | SQLite / SQLAlchemy | **READY** | **INTEGRATED** | `test_multi_tenancy.py` | Global | Scoped merchant queries |
| **Deterministic Demo System** | `scripts/reset_demo.py`, `backend/app/api/` | `DemoControlView.tsx` | `/api/v1/agent/scenarios/reset` | Seed Data | None | **READY** | **INTEGRATED** | `test_e2e_agent.py` | `/demo` | 1-Click state reset |
