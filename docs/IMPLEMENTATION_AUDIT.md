# Implementation & Codebase Audit: Security Perimeter & CTI Extension

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  
**Status**: Comprehensive Codebase Audit Complete  

---

## 1. Executive Summary

This audit establishes a strict roadmap for extending the validated Risk Manager Agent with:
1. **Cloudflare Security Perimeter** (Edge WAF, Rate Limiting, API Shield, Bot/Turnstile telemetry).
2. **End-to-End Cryptographic Protection & Dynamic Masking** (Field-level encryption, role-based masking, AES-256-GCM, key lifecycle).
3. **Comprehensive DLP Gates** (Luhn PAN scrubber, secrets detector across input, database, agent, logs, and output).
4. **Enhanced Card Exposure & Threat Intelligence** (Normalized CTI feeds, multi-source correlation, temporal decay).
5. **Integrated SOC / Security Center UI** (Cloudflare edge telemetry, Card exposure timeline, Data protection dashboard).

---

## 2. Component Inventory & Classification

| Component | Current State | Classification | Action Plan |
| :--- | :--- | :--- | :--- |
| **Risk Scoring Engine (`risk_scorer.py`)** | Deterministic 6-factor composite ($0-100$) | **DO NOT TOUCH** | Preserved as authoritative scoring kernel. |
| **Policy Guardrail Engine (`policy_engine.py`)** | Centralized 5-tier response ($T=40, T=75$) | **DO NOT TOUCH** | Preserved as authoritative policy boundary. |
| **Risk Manager Agent (`risk_agent.py`)** | Dynamic 4-level investigation with tool audit | **ADAPT** | Ingest normalized Cloudflare signals and rich CTI evidence without altering baseline score semantics. |
| **Threat Intel Provider (`threat_intel/`)** | Base abstraction + Synthetic provider | **EXTEND** | Add rich exposure schemas, multi-source correlation, and provider health checks. |
| **Database Entities (`entities.py`)** | 10 core tables (Cards, Tokens, Cases, etc.) | **EXTEND** | Add `CloudflareSecurityEvent`, `DLPEvent`, `KeyMetadata` without duplicating existing entities. |
| **API Endpoints (`routes_*.py`)** | Risk, Cards, Cases, Tokens, Audit, Evaluation | **EXTEND** | Add `/security/*`, `/exposure/*`, `/health/*` without duplicating existing endpoints. |
| **Security Layer (`security/`)** | HMAC-SHA256, regex DLP, sanitization | **EXTEND** | Add AES-256-GCM field encryption, KeyProvider, dynamic masking policy, and request/response DLP gates. |
| **Cloudflare Adapter (`integrations/`)** | Conceptual / Direct | **NEW** | Build `CloudflareAdapter` with WAF, Bot, Rate-limit, and Ray ID telemetry parsing. |
| **Frontend SOC Dashboard (`frontend/src/`)** | Timeline, Evaluation, Risk Stream, Cases, Audit | **EXTEND** | Add Security Center (`/security`), Data Protection (`/security/data-protection`), and Card Exposure Overview. |

---

## 3. Detailed Audit Matrix

### CURRENT (What Already Exists and Works)
- **FastAPI Gateway**: Asynchronous REST endpoints for risk scoring, token lifecycle, card inventory, and audit ledger.
- **Deterministic Risk Engines**: `TransactionRiskEngine`, `CardRiskEngine`, `TokenRiskEngine`, `ExposureCorrelationEngine`, `RiskScoringEngine`.
- **Policy Engine**: Strict 5-tier gating (`LOW`, `MONITOR`, `STEP_UP`, `REVIEW`, `AUTO_REMEDIATE`).
- **Cryptographic Boundary**: HMAC-SHA-256 PAN fingerprinting, DLP regex redaction.
- **Audit Ledger**: Hash-chained SHA-256 audit trail (`curr_hash = SHA256(data + prev_hash)`).
- **Test Suite**: 45 passing automated backend tests (`pytest -v`).

### REUSABLE (Internal & External Components to Leverage)
- Reusable SQLite/SQLAlchemy ORM session management and schemas.
- Reusable Razorpay adapter abstractions (`MockRazorpayAdapter`, `RazorpayTestAdapter`).
- Reusable React components: `InvestigationTimeline`, `LiveRiskTable`, `EvaluationDashboard`.
- Reusable DLP Luhn validation logic from open-source patterns (`Data-Loss-Prevention` / `Watcher`).
- Reusable threat indicator models and normalization patterns (`ThreatDeck` / `mcp-threatintel`).

### MISSING (To Build in This Extension)
- Comprehensive **Dynamic Masking Engine** (`backend/app/security/masking.py`) supporting role-based context masks.
- Formal **Field-Level Encryption & Key Provider** (`backend/app/security/encryption.py`, `backend/app/security/key_provider.py`) using AES-256-GCM.
- **Cloudflare Edge Adapter & Security Event Model** (`backend/app/integrations/cloudflare_adapter.py`, `CloudflareSecurityEvent`).
- **Comprehensive DLP Gate Decorators / Middleware** protecting API inputs, DB writes/reads, logs, and agent I/O.
- **Security Center & Data Protection UI Tabs** in the React dashboard.
- **1-Click Pre-Deployment Verification Script** (`scripts/pre_deploy.py`).

### DUPLICATED / RISKY (Anti-Patterns to Avoid)
- **DO NOT** create a second risk scoring scale or independent exposure blocking rules.
- **DO NOT** store raw PANs, CVVs, PINs, or auth secrets in any database, cache, or state store.
- **DO NOT** allow Cloudflare WAF signals to bypass the deterministic policy engine.
- **DO NOT** alter the frozen evaluation dataset (`evaluation/test.jsonl`, hash `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`).
