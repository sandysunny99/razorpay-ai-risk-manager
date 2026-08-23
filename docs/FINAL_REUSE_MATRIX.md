# Final Reuse Matrix & Reference Repository Evaluation

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  
**Status**: Comprehensive Open-Source & Internal Reuse Audit Complete  

---

## 1. Reference Repositories & Reuse Decisions

| Reference Repository | Primary Capabilities | License | Useful Patterns & Components | Reuse Decision | Integration Strategy & Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Data Loss Prevention** (`Weedant/Data-Loss-Prevention`) | Card pattern detection, sensitive data redaction | MIT | Luhn checksum algorithm, regex card scrapers, log masking pipelines | **REUSE / ADAPT** | Extracted and hardened into `backend/app/security/dlp.py` and `masking.py` for comprehensive input/output/log DLP. |
| **MCP Threat Intelligence** (`pete-builds/mcp-threatintel`) | Threat provider abstraction, IOC lookup schemas | MIT | Decoupled `ThreatIntelProvider` interface, normalized JSON schemas | **ADAPT** | Adapted into `backend/app/threat_intel/base.py` and synthetic offline provider with source reliability metrics. |
| **Thales Watcher** (`thalesgroup-cert/Watcher`) | Enterprise CTI platform, leak monitoring | Apache 2.0 | Multi-source breach models, SOC investigation queues, confidence scoring | **ADAPT** | Adapted for multi-source breach correlation and structured `ExposureEvent` models. |
| **ThreatDeck** (`gripebomb/ThreatDeck`) | Threat deck feeds, deduplication, enrichment | MIT | Indicator deduplication, temporal decay formulas, feed reliability | **ADAPT** | Adapted into temporal freshness calculations and stealer dump matchers. |
| **OSINT PH Threat Platform** (`osintph/threatintel-platform`) | Threat intelligence collector architecture | GPL-3.0 / MIT | Feed normalization patterns, dark-web breach data models | **REFERENCE ONLY** | Architectural reference for normalized threat feeds without copying GPL-encumbered source code. |
| **AI Threat Intel Banking** (`Dhruvvv-26/AI-Threat-Intelligence-Banking`)| Banking fraud detection, risk scoring | MIT | Transaction risk factors, foreign geo-distance heuristics | **REFERENCE ONLY** | Validated our 6-dimension mathematical weighting model ($25/25/15/15/10/10$). |
| **ThreatForge** (`brunoaugusto1978/threatforge`) | Threat indicator lifecycle | MIT | Threat state management, incident lifecycle | **REFERENCE ONLY** | Conceptual reference for security case statuses (`OPEN`, `INVESTIGATING`, `RESOLVED`). |

---

## 2. Internal Core Reuse Matrix

| Capability / Layer | Existing Project Component | Reuse Decision | Rationale |
| :--- | :--- | :--- | :--- |
| **Risk Scoring Kernel** | `backend/app/engines/risk_scorer.py` | **100% REUSE** | Authoritative 6-factor composite score ($0-100$). Zero duplicate risk engines. |
| **Policy Guardrails** | `backend/app/engines/policy_engine.py` | **100% REUSE** | Centralized 5-tier response boundaries ($T=40, T=75$). Zero duplicate policy ladders. |
| **Risk Manager Agent** | `backend/app/agent/risk_agent.py` | **REUSE & EXTEND** | Dynamic investigation levels (0-3) with explicit tool audit. Extended with Cloudflare telemetry. |
| **Gateway Adapters** | `backend/app/integrations/razorpay_adapter.py`| **100% REUSE** | `MockRazorpayAdapter` and `RazorpayTestAdapter` for safe sandbox testing. |
| **Cryptographic Audit**| `backend/app/engines/audit_ledger.py` | **100% REUSE** | SHA-256 hash-chained tamper-evident audit trail with 1-click verification. |
| **Database & ORM** | `backend/app/models/entities.py` | **REUSE & EXTEND** | Existing 10 tables preserved; extended with Cloudflare and DLP tracking. |
| **Frontend SOC UI** | `frontend/src/App.tsx` & components | **REUSE & EXTEND** | React 18 dashboard extended with Security Center and Card Exposure Overview. |
