# Razorpay Risk Manager Agent

<div align="center">

![Razorpay Risk Manager Banner](https://img.shields.io/badge/Razorpay-Risk%20Manager%20Agent-0D83FF?style=for-the-badge&logo=shield&logoColor=white)
![Build Status](https://img.shields.io/badge/Build-Passing-10B981?style=for-the-badge)
![Security Standard](https://img.shields.io/badge/Security-PCI--Aware%20Design%20%7C%20HMAC--SHA--256%20PAN%20Fingerprinting-6366F1?style=for-the-badge)
![Hackathon Track](https://img.shields.io/badge/Track-Risk%20Manager-F59E0B?style=for-the-badge)

**"An agentic security layer for payment risk, card exposure, token protection, and policy-controlled remediation."**

</div>

---

## 🎯 Overview & Product Vision

Payment risk rarely appears as a single obvious fraudulent transaction. In modern cybercrime ecosystems, risk emerges from the correlation of fragmented signals:
- **Card exposure** on dark-web stealer logs and paste dumps (supported via pluggable threat provider architecture)
- **Active payment tokens** left vulnerable to unauthorized exploitation
- **Zombie tokens** persisting in vaults on expired/cancelled cards
- **Transaction velocity and cross-border geographic anomalies**
- **Customer behavioral deviations**

The **Razorpay Risk Manager Agent** is an autonomous prototype risk orchestration system designed for Razorpay's payment ecosystem that executes the complete risk lifecycle:

$$\text{OBSERVE} \longrightarrow \text{DETECT} \longrightarrow \text{INVESTIGATE} \longrightarrow \text{CORRELATE} \longrightarrow \text{REASON} \longrightarrow \text{ASSESS RISK} \longrightarrow \text{CHECK POLICY} \longrightarrow \text{ACT} \longrightarrow \text{VERIFY} \longrightarrow \text{AUDIT}$$

---

## 🚀 Key Innovations & Capabilities

1. **HMAC-SHA-256 PAN Fingerprinting**: Raw PANs, CVVs, and PINs are **never stored, logged, or sent to an LLM**. Exposure feeds are matched using one-way HMAC-SHA-256 cryptographic fingerprints.
2. **Deterministic Zombie Token Detection**: Continuously monitors the portfolio to identify active vault tokens attached to expired or blocked cards, eliminating recurring liability.
3. **Pluggable Threat Intelligence Abstraction**: Decoupled `ThreatIntelProvider` supporting offline high-fidelity synthetic scenarios (9 test cases), breach dumps, and dark-web stealer feeds.
4. **Policy Guardrail Engine**: The AI Agent never acts unconstrained. Actions are strictly gated:
   - `AUTO_EXECUTE`: Token revocation on critical risk / zombie tokens
   - `REVIEW_REQUIRED`: Card suspension (high customer friction)
   - `NEVER_EXECUTE`: Financial transfers / refunds
5. **Verified State Transition**: Employs the `ACT → VERIFY → RECALCULATE` loop to verify gateway state transitions before updating risk scores.
6. **Tamper-Evident Hash-Chained Audit Ledger**: All agent decisions and gateway remediations are chained with SHA-256 hashes (`curr_hash = SHA256(data + prev_hash)`), providing cryptographic verification against tampering.
7. **SOC Security Dashboard**: High-fidelity React dashboard with live agent execution timelines, risk badges, zombie token monitors, and cryptographic audit validation.

---

## 🏗️ Architecture Summary

```
                         USER / MERCHANT / WEBHOOK
                                    │
                                    ▼
                        FASTAPI RISK GATEWAY
                                    │
                      RISK MANAGER AGENT LOOP
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
 DETERMINISTIC ENGINES       THREAT INTELLIGENCE        POLICY GUARDRAILS
 • Transaction Risk           • Synthetic Provider       • AUTO_EXECUTE
 • Card Risk (Expiration)     • Stealer Logs             • REVIEW_REQUIRED
 • Token Risk & Zombie Token  • Dark-Web Pastes          • NEVER_EXECUTE
 • Exposure Correlation       • BIN Intelligence                 │
       └────────────────────────────┬────────────────────────────┘
                                    │
                       COMPOSITE RISK (0 - 100)
                                    │
                         RESPONSE & REMEDIATION
                       • Revoke Token on Gateway
                       • Query Gateway Verification
                       • Recalculate Risk (94 → 21)
                       • Immutable Audit Record
```

---

## ⚡ Quickstart & Local Deployment

### 1. Backend Service (FastAPI)
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Run automated test suite (15 tests passing)
pytest -v

# Start FastAPI Risk Gateway
uvicorn app.main:app --app-dir backend --reload --port 8000
```
- Interactive Swagger API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/`

### 2. Frontend SOC Dashboard (React + Vite + Tailwind)
```bash
cd frontend
npm install
npm run dev
```
- SOC Dashboard UI: `http://localhost:5173/`

---

## 🎬 1-Click Golden Demo Scenario

In the SOC Dashboard, click **"Execute Golden Attack Demo (₹18,500)"**:
1. **Transaction Arrives**: Customer `1042` attempts a ₹18,500 authorization from Moscow (velocity: 4 attempts).
2. **Anomalies Detected**: Amount deviation (+20), Geo mismatch (+15), Velocity (+14).
3. **Breach Correlated**: Card fingerprint matched in `Telegram/RedLine-Stealer-Dump-08` (+25).
4. **Initial Risk**: **94/100 (CRITICAL)**.
5. **Policy Evaluated**: Token revocation permitted under Policy `PR-01`.
6. **Autonomous Action**: Agent revokes token `tok_test_123`.
7. **Gateway Verification**: Query confirmed `REVOKED`.
8. **Risk Recalculated**: Drops **94 → 21 (LOW)**.
9. **Case & Audit**: Security Case `CASE-2026-XXXX` created and stored in immutable audit ledger.

---

## 📚 Technical Documentation Index

- [ARCHITECTURE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/ARCHITECTURE.md) - System architecture, data flow & modular design
- [SECURITY.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/SECURITY.md) - Cryptographic boundary, HMAC fingerprinting, DLP & threat sanitization
- [THREAT_INTELLIGENCE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/THREAT_INTELLIGENCE.md) - Feed ingestion, provider abstraction & synthetic scenarios
- [AGENT_DESIGN.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/AGENT_DESIGN.md) - Agent loop, tool registry & reasoning architecture
- [RISK_ENGINE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/RISK_ENGINE.md) - Mathematical risk scoring formulas & factor breakdown
- [POLICY_ENGINE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/POLICY_ENGINE.md) - Guardrail rules, decision matrix & approvals
- [API.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/API.md) - Complete REST API specification
- [DEPLOYMENT.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/DEPLOYMENT.md) - Local & production deployment guide
- [TESTING.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/TESTING.md) - Test strategy, automated suites & validation results
- [REUSE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/REUSE.md) - Reference repository analysis & reuse matrix
- [HACKATHON_DEMO.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/HACKATHON_DEMO.md) - End-to-end demo walkthrough guide
