# Razorpay AI Risk Manager: System Architecture & Operations Specification

**Release Version**: `v2.1.0-preview`  
**Hackathon Track**: Razorpay AI Buildathon 2026 — AI Risk Manager  
**Repository**: `sandysunny99/razorpay-ai-risk-manager`  
**Benchmark Test Set**: Frozen $N=300$ (Positive: 67, Negative: 233, SHA-256: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`)

---

## 1. Executive Summary & Core Value Proposition

The Razorpay AI Risk Manager Agent is an autonomous, dual-layer threat mitigation and credential protection system designed for payment gateways and merchants. It solves the critical industry trade-off between **risk detection sensitivity** and **business disruption**.

### Key Differentiators:
1. **Dual-Layer Decision Architecture**:
   - **Broad Detection ($T = 40.0$)**: Captures **88.06% of all suspicious anomalies** for active investigation and step-up challenges.
   - **Auto-Action Threshold ($T = 75.0$)**: Operates at **100.00% precision (0 false positives)** for automated token revocation and risk blocking.
2. **Zombie Card Saver Module**:
   - Disruption-prevention engine that identifies stale/expired/blocked cards with active dependent tokens.
   - Selectively revokes compromised tokens while preserving critical recurring subscriptions (e.g. Netflix, SaaS, utilities).
3. **Defense-in-Depth & Zero-Knowledge Security**:
   - Luhn-aware DLP scanning strips PANs and credentials from logs and LLM contexts.
   - HMAC-SHA256 salted card fingerprinting enables breach correlation without raw card exposure.
   - Cryptographic SHA-256 chained audit ledger guarantees non-repudiation and forensic compliance.

---

## 2. End-to-End Component Topology

```
+-----------------------------------------------------------------------------------+
|                                1. INGESTION LAYER                                 |
|  • Razorpay Test Mode Webhook (/api/v1/webhooks/razorpay)                         |
|  • Cloudflare Edge Security Telemetry (/api/v1/security/cloudflare/events)        |
|  • Event Deduplication (TTL Idempotency Tracker)                                  |
|  • Enterprise DLP Sanitization Gate                                               |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                                2. ENRICHMENT LAYER                                |
|  • Binlist / IIN Provider (6-8 digit BIN metadata, caching, rate limiting)        |
|  • URLhaus Threat Feed (Malware domain IOC matching & safe caching)               |
|  • In-Memory Pub/Sub EventBus                                                     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           3. AUTHORITATIVE RISK ENGINES                           |
|  • Transaction Risk Engine (Velocity, Amount, Currency, Device)                   |
|  • Card Risk Engine (Lifecycle, Failed Auth, Chargeback History)                  |
|  • Token Risk Engine (Vault State, Hijack Risk, Inactivity)                       |
|  • Exposure Correlation Engine (Dark Web, Stealer Logs, IOC Matches)              |
|  • Customer / Merchant Multi-Tenant Isolation Engine                              |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                         4. DYNAMIC AGENT & POLICY ENGINE                          |
|  • Read-Only Specialized Investigation Tools (9 Agent Tools)                      |
|  • Prompt Injection Shield & System Prompt Defense                                |
|  • 5-Tier Policy Execution Engine (Low, Monitor, Step-Up, Review, Auto-Remediate) |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        5. ZOMBIE CARD SAVER & REMEDIATION                         |
|  • Credential Lifecycle State Machine                                             |
|  • Token Dependency Graph & Merchant Impact Calculator                            |
|  • Selective Remediation Protocol (Preserves Subscriptions, Revokes High-Risk)    |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                         6. AUDIT, LEDGER & OBSERVABILITY                          |
|  • Cryptographic SHA-256 Chained Block Ledger                                     |
|  • SOC Security Center Dashboard & Live Risk Streaming View                       |
|  • Reproducible Evaluation Benchmark Dashboard                                    |
+-----------------------------------------------------------------------------------+
```

---

## 3. Subsystem Breakdown

### 3.1 Ingestion & Gateway Adapter (`backend/app/integrations/`, `backend/app/events/`)
- Ingests test-mode transactions, webhook notifications, and simulated Cloudflare edge signals.
- Verifies cryptographic HMAC-SHA256 signatures over raw request bytes.
- Implements thread-safe idempotency tracking to prevent duplicate ingestion.

### 3.2 Bounded Enrichment Layer (`backend/app/enrichment/`)
- Interfaces with bounded public telemetry feeds:
  - **Binlist Provider**: Extracts scheme, issuer bank, and card brand without full PAN exposure.
  - **URLhaus Threat Provider**: Scans transaction metadata against active malware and phishing domains.
- Equipped with in-memory TTL caching and offline mock providers for high-availability test environments.

### 3.3 Zombie Card Saver Module (`backend/app/zombie_card_saver/`)
- Evaluates the lifecycle disparity between inactive payment cards and active dependent tokens.
- Constructs token dependency topologies to distinguish high-risk one-off tokens from business-critical recurring billing.
- Exposes dedicated SOC operations routes under `/api/v1/zombie-cards`.

### 3.4 SOC Frontend Architecture (`frontend/src/`)
- **React 18 + TypeScript + Vite + Tailwind CSS**
- Primary SOC Navigation Views:
  1. **Zombie Card Saver View**: Interactive token topology graph, merchant disruption index, and selective revocation controls.
  2. **Agent Investigation Timeline**: Step-by-step reasoning trace and explainable risk factor weights.
  3. **SOC Security Center & DLP**: Real-time DLP violation telemetry and Cloudflare WAF events.
  4. **Threat Intelligence & Exposure**: Card fingerprint breach correlation and dark-web telemetry.
  5. **Model Evaluation & Metrics**: Live confusion matrix and evaluation metrics over the held-out test set.
  6. **Tamper-Evident Audit Trail**: Chained block hash inspection and cryptographic verification.

---

## 4. Benchmark Verification Standard

The system evaluation is rigorously tested against `evaluation/test.jsonl`:
- **Sample Size ($N$)**: 300 held-out samples (67 positive, 233 negative).
- **Auto-Action Precision ($T=75.0$)**: **100.00%** (0 false positives).
- **Broad Recall ($T=40.0$)**: **88.06%** sensitivity across anomaly screenings.
- **SHA-256 Frozen Checksum**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`.
