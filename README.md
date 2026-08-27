# Razorpay AI Risk Manager Agent

<div align="center">

![Razorpay Risk Manager Banner](https://img.shields.io/badge/Razorpay-AI%20Risk%20Manager%20Agent-0D83FF?style=for-the-badge&logo=shield&logoColor=white)
![Build Status](https://img.shields.io/badge/Build-Passing%20(54%20Tests)-10B981?style=for-the-badge)
![Autonomous Precision](https://img.shields.io/badge/Auto--Action%20Precision-100.0%25%20(0%20FP)-6366F1?style=for-the-badge)
![Detection Recall](https://img.shields.io/badge/Detection%20Recall-88.06%25%20(T=40.0)-3B82F6?style=for-the-badge)
![Security Standard](https://img.shields.io/badge/Security-PCI--Aware%20Design%20%7C%20HMAC--SHA--256%20PAN%20Fingerprinting-8B5CF6?style=for-the-badge)
![Hackathon Track](https://img.shields.io/badge/Track-AI%20Risk%20Manager%20(2026)-F59E0B?style=for-the-badge)

**"Razorpay AI Risk Manager is an agentic payment-risk prototype that detects suspicious activity, investigates correlated evidence, applies policy-controlled responses, and verifies security actions."**

</div>

---

## 🎯 1. Target Loss Class & Problem Statement

- **Single Target Loss Class**: *"Loss caused by compromised payment credentials being used in suspicious transactions."*
- **The Core Problem**: Compromised payment credentials cause financial losses before traditional static risk rules react. However, naive binary blocking (e.g. `Risk >= 75 -> BLOCK`, else `PASS`) creates a false dilemma between missing fraud and interrupting legitimate customer checkouts.
- **The Solution**: An explainable, tiered agentic payment-risk architecture that detects broadly, correlates cross-domain evidence (transaction, card, token lifecycle, CTI stealer feeds, edge signals), and responds progressively across 5 tiers—automating irreversible vault token destruction only at high confidence ($T=75$).

---

## 🤖 2. Why It Is Agentic (Not Just an LLM)

We do not define "agentic" as simply calling an LLM. True agentic execution in this system consists of an end-to-end autonomous perception, reasoning, and closed-loop execution lifecycle:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 1. OBSERVE  │───▶│2.INVESTIGATE│───▶│3. CORRELATE │───▶│  4. REASON  │
│ Detect risk │    │Select tools │    │Fuse CTI,card│    │Evidence-    │
│ trigger event│   │(Levels 0-3) │    │& token data │    │grounded score│
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────▼──────┐
│  8. AUDIT   │◀───│  7. VERIFY  │◀───│   6. ACT    │◀───│  5. DECIDE  │
│SHA-256 chain│    │Confirm state│    │Execute tier │    │Invoke Policy│
│ledger block │    │recalculation│    │defensive step│   │guardrails   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

1. **OBSERVE**: Intercept incoming payment authorization request on FastAPI gateway.
2. **INVESTIGATE**: Dynamically escalate tool execution depth (Levels 0–3) based on risk factors rather than executing static pipelines.
3. **CORRELATE**: Fuse multi-domain signals—transaction velocity, geo distance, card expiration, token lifecycle, dark-web stealer log dumps, and edge telemetry.
4. **REASON**: Synthesize structured risk findings with mathematical factor attribution ($25/25/15/15/10/10$).
5. **DECIDE**: Consult centralized Policy Guardrails (`AUTO_EXECUTE`, `REVIEW_REQUIRED`, `NEVER_EXECUTE`).
6. **ACT**: Issue progressive defensive response (Step-Up 2FA, Case escalation, or Razorpay Vault token revocation).
7. **VERIFY**: Query Razorpay adapter to confirm state transition (`REVOKED`), recalculating composite risk ($94 \rightarrow 16$).
8. **AUDIT**: Persist decision trace in a tamper-evident SHA-256 hash-chained immutable audit ledger.

---

## ⚖️ 3. Two-Layer Risk Architecture

Detection sensitivity and autonomous remediation have fundamentally different risk tolerances:

```
                                LAYER 1: BROAD DETECTION (T = 40.0)      LAYER 2: AUTONOMOUS ACTION (T = 75.0)
ACTUAL POSITIVE (Pos=67)        TP = 59              FN = 8              TP = 35              FN = 32 (Score 40-74)
ACTUAL NEGATIVE (Neg=233)       FP = 0               TN = 233            FP = 0               TN = 233
```

- **Layer 1: Broad Risk Detection ($T = 40.0$)**: Intercepts **$88.06\%$ of attack patterns** with high recall, flagging suspicious activity for step-up or analyst review.
- **Layer 2: Autonomous Auto-Remediation ($T = 75.0$)**: Authorizes irreversible token revocation on Razorpay Vault with **$100.0\%$ Precision ($0$ False Positives)**.
- **Sub-Critical Risk Band ($40.0 \le \text{Risk} < 75.0$)**: The 32 detected cases below $T=75$ are not detector misses—they are routed to non-destructive Step-Up 2FA challenges or SOC review.

---

## 🛡️ 4. Five Progressive Response Tiers

```
  Risk Score:  0 -------- 34.9 -------- 39.9 -------- 64.9 -------- 74.9 -------- 100
  Response:     [ Tier 0: LOW ] [ Tier 1: MON ] [ Tier 2: STEP ] [ Tier 3: REV ] [ Tier 4: AUTO ]
  Action:            ALLOW          MONITOR        REQUEST_STEP_UP   SOC REVIEW     REVOKE_TOKEN
  Investigation:    Level 0         Level 1           Level 2          Level 2        Level 3
```

1. **Tier 0: LOW RISK ($0.0 - 34.9$)**: Fast-path authorization (`ALLOW`), skips heavy CTI lookups.
2. **Tier 1: MONITOR ($35.0 - 39.9$)**: Telemetry logging (`MONITOR`) for baseline variance tracking.
3. **Tier 2: STEP_UP ($40.0 - 64.9$)**: Simulated 2FA/OTP challenge (`REQUEST_STEP_UP`) with post-verification risk recalculation ($54 \rightarrow 27$).
4. **Tier 3: REVIEW ($65.0 - 74.9$)**: Security case escalation (`REVIEW_REQUIRED`) for SOC review.
5. **Tier 4: AUTO_REMEDIATE ($\ge 75.0$ or Zombie Token)**: Autonomous token revocation (`AUTO_EXECUTE`) on Razorpay Vault with mandatory verification.

---

## 🔍 5. Card Exposure & Zombie Token Intelligence

- **HMAC-SHA-256 PAN Fingerprinting**: Raw card PANs, CVVs, and OTPs are **never stored, logged, or sent to external threat feeds or LLMs**. Exposure intelligence matches synthetic dark-web stealer dumps using salted HMAC-SHA-256 fingerprints with Luhn pre-validation.
- **Exposure Is Evidence**: Card exposure feeds the authoritative deterministic Risk Scorer; it does not bypass the policy engine.
- **Zombie Token Detection**: Identifies payment tokens that remain active on the gateway vault after the underlying physical card has expired, been replaced, or reported compromised.

---

## 🌐 6. Defense-in-Depth & Cloudflare Edge Protection

Security is structured as a defense-in-depth perimeter:

- **Edge Perimeter (Cloudflare Adapter)**: Ingests normalized WAF action telemetry, `CF-Ray` request tracing, and standard Cloudflare 1–99 bot scores (`VERIFIED_BOT=1`, `LIKELY_AUTOMATED=2..29`, `LIKELY_HUMAN=30..99`).
- **Data at Rest**: AES-256-GCM authenticated encryption with NIST-standard 96-bit nonces and a versioned KMS key provider.
- **Data Loss Prevention (DLP)**: Proactive runtime regex and Luhn algorithm scrubber scanning API inputs, database writes, agent reasoning summaries, and logs to redact card numbers and API secrets (`rzp_live_...`).
- **Dynamic Masking**: Server-side masking across PANs (`**** 4921`), emails (`a***d@razorpay.com`), and IPs.
- **Tenant Isolation**: Strict `merchant_id` query scoping blocking cross-tenant IDOR access.
- **Cryptographic Audit Ledger**: Immutable SHA-256 hash-chained block records.

---

## 📊 7. Measured Evaluation Results (Frozen Held-Out Test Set $N = 300$)

> **Note**: Measured results on the frozen held-out test set (`SHA-256: 76a26e7c...`). These represent empirical test benchmark metrics, not production guarantees.

| Metric Dimension | Layer 1: Broad Detection ($T=40.0$) | Layer 2: Auto-Action ($T=75.0$) | Status / Benchmark |
| :--- | :--- | :--- | :--- |
| **Precision** | **100.00%** ($1.0000$) | **100.00%** ($1.0000$) | **0 False Positives on Held-Out Set** |
| **Recall (Sensitivity)** | **88.06%** (59 / 67 attacks) | **52.24%** (35 / 67 attacks) | **High Recall vs. High Precision Tiers** |
| **Accuracy** | **97.33%** ($0.9733$) | **89.33%** ($0.8933$) | **High Overall Accuracy** |
| **False Positive Rate (FPR)** | **0.00%** ($0.0000$) | **0.00%** ($0.0000$) | **Zero Legitimate Disruption in Test Set** |
| **F1 Score** | **0.9365** | **0.6863** | **Optimal Threshold Balance** |
| **Illustrative Expected Cost** | **₹40,000** | **₹160,000** | **₹120,000 Illustrative Reduction ($75\%$ drop)** |
| **Automated Backend Tests** | **63 / 63 Passed (100%)** | Pytest Unit, Security, DLP, IDOR, Audit | **ALL PASS (1.88s)** |

*Cost assumptions for illustrative model: $C_{FP} = ₹100$, $C_{FN} = ₹5,000$.*

---

## 🎬 8. 5-Minute Golden Demo Runbook

In the SOC Dashboard (`http://localhost:5173`), click **"Golden Demo Scenario: Stealer Dump + Zombie Token"**:

1. **00:00 - 00:30 (Problem & Overview)**: Present SOC dashboard telemetry and the dual-threshold architecture.
2. **00:30 - 01:30 (Suspicious Transaction)**: Customer `1042` attempts a ₹18,500 authorization from Moscow. Velocity: 4 attempts.
3. **01:30 - 02:15 (Correlated Investigation)**: Agent executes Level 3 investigation, correlating RedLine Stealer log match ($96\%$ confidence), geo mismatch, and expired card on active vault token `tok_test_123`.
4. **02:15 - 03:00 (Risk & Policy Decision)**: Composite risk scored at **94 / 100 (CRITICAL)**. Policy Engine authorizes token revocation under Policy `PR-01`.
5. **03:00 - 03:45 (Autonomous Action & Verification)**: Token revoked on Razorpay Vault adapter $\rightarrow$ Gateway confirms `REVOKED` $\rightarrow$ Risk drops from **94 → 16 (LOW)**.
6. **03:45 - 04:30 (Audit & Security Center)**: Security Case committed to SHA-256 hash ledger. Open **Security Center** to run interactive DLP sandbox test with synthetic card `4111 1111 1111 1111`.
7. **04:30 - 05:00 (Evaluation & Closing Pitch)**: Navigate to Evaluation Dashboard to demonstrate side-by-side confusion matrices and deliver closing pitch.

---

## ❓ 9. Evaluator FAQ & Security Questions

- **Q: Why use two thresholds?**  
  *A: Broad detection ($T=40$) and autonomous remediation ($T=75$) have different risk tolerances. $T=40$ catches threats with $88.06\%$ recall for non-destructive Step-Up or review, while $T=75$ protects against false positives ($100\%$ precision) for irreversible vault token revocation.*
- **Q: Is this live Razorpay or live Cloudflare?**  
  *A: It uses a safe Test Mode/Mock Razorpay adapter and a Cloudflare-compatible telemetry adapter for offline, repeatable evaluation.*
- **Q: Is it PCI compliant?**  
  *A: It is a PCI-aware prototype implementing payment data minimization, HMAC fingerprinting, DLP, and encryption controls.*
- **Q: Can the AI transfer money?**  
  *A: No. Financial movement is strictly gated under Policy `NEVER_EXECUTE`.*

---

## ⚡ 10. Quickstart & Deployment Runbook

### 1. Verify Test Set Integrity & Pre-Deploy Gates
```powershell
python scripts/verify_test_set.py
python scripts/pre_deploy.py
```

### 2. Run Backend Test Suite (63 Tests) & Evaluation Benchmark
```powershell
pytest -q
python scripts/run_final_evaluation.py
```

### 3. Start Backend Gateway (FastAPI)
```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
- API Documentation: `http://localhost:8000/docs`
- Health Probe: `http://localhost:8000/health`

### 4. Start Frontend SOC Dashboard (React + Vite)
```powershell
cd frontend
npm install
npm run dev
```
- SOC Dashboard: `http://localhost:5173/`

### 5. Deterministic Demo Reset
```powershell
python scripts/reset_demo.py
```

---

## ⚠️ 11. Known Limitations & Prototype Scope

1. **Prototype Scope**: Built as a PCI-aware prototype; not a formally certified PCI-DSS Level 1 payment gateway.
2. **Evaluation Set**: Metrics measured on a 2,000-record synthetic payment risk evaluation dataset.
3. **Gateway & Edge Modes**: Uses adapter-normalized simulations (`SIMULATED`, `TEST_MODE / MOCK`, `SYNTHETIC`) for offline evaluation.

---

## 📚 12. Technical Documentation Index

- [docs/FINAL_DEPLOYMENT_STATUS.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_DEPLOYMENT_STATUS.md) - Final Deployment & Submission Status Specification (v2.0.0-rc1)
- [docs/GITHUB_DEPLOYMENT.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/GITHUB_DEPLOYMENT.md) - GitHub Repository & CI Pipeline Specification
- [docs/RENDER_DEPLOYMENT.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/RENDER_DEPLOYMENT.md) - Render Cloud Deployment Specification
- [docs/CLOUDFLARE_DEPLOYMENT.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/CLOUDFLARE_DEPLOYMENT.md) - Cloudflare Edge Perimeter Deployment Specification
- [docs/LIVE_APPLICATION_TEST.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/LIVE_APPLICATION_TEST.md) - Live Application Smoke Test & Verification Record
- [docs/FINAL_RELEASE_TRUTH_MATRIX.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_RELEASE_TRUTH_MATRIX.md) - Final Release Truth & Allowed Claims Matrix (v2.0.0-rc1)
- [docs/FINAL_RELEASE_STATUS.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_RELEASE_STATUS.md) - Final Release Status Specification (v2.0.0-rc1)
- [docs/FINAL_RELEASE_EVIDENCE_MATRIX.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_RELEASE_EVIDENCE_MATRIX.md) - Final Release Evidence Matrix (v2.0.0-rc1)
- [docs/FINAL_SUBMISSION_CHECKLIST.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_SUBMISSION_CHECKLIST.md) - Final Hackathon Submission Checklist & Release Sign-Off
- [docs/LIVE_SECURITY_VERIFICATION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/LIVE_SECURITY_VERIFICATION.md) - Live Security Verification & Data Boundary Inspection Report
- [docs/LIVE_BROWSER_E2E.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/LIVE_BROWSER_E2E.md) - Live Browser End-to-End (E2E) Test & Presentation Walkthrough
- [docs/LIVE_DEPLOYMENT_RESULT.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/LIVE_DEPLOYMENT_RESULT.md) - Live Deployment Result & Public Service Specification
- [docs/DOCKER_VERIFICATION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/DOCKER_VERIFICATION.md) - Docker Containerization & Multi-Stage Image Verification
- [docs/FINAL_SYSTEM_ARCHITECTURE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_SYSTEM_ARCHITECTURE.md) - Final System Architecture & Defense-in-Depth Specification
- [docs/CLOUDFLARE_SECURITY_ARCHITECTURE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/CLOUDFLARE_SECURITY_ARCHITECTURE.md) - Cloudflare Security Perimeter & Edge Architecture
- [docs/CARD_EXPOSURE_ARCHITECTURE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/CARD_EXPOSURE_ARCHITECTURE.md) - Card Exposure Architecture & HMAC Threat Correlation
- [docs/CRYPTOGRAPHIC_DATA_PROTECTION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/CRYPTOGRAPHIC_DATA_PROTECTION.md) - Cryptographic Data Protection & Key Management
- [docs/DEMO_RUNBOOK.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/DEMO_RUNBOOK.md) - Step-by-step live demo presentation runbook

## 🌐 Optional Free API Integrations

All integrations degrade gracefully — the demo works with **zero configuration**.
Real API keys enhance risk scoring with live data when available.

| API | Use Case | Free Tier | Setup |
|-----|----------|-----------|-------|
| ip-api.com | Real geo-deviation scoring | 45 req/min, no auth | Auto-enabled (ENABLE_IP_GEO=true) |
| Have I Been Pwned v3 | Dark web breach correlation | Unlimited* | Set HIBP_API_KEY |
| AbuseIPDB | IP reputation scoring | 1,000/day | Set ABUSEIPDB_API_KEY |
| Upstash Redis | Multi-worker rate limiting | 10K req/day | Set REDIS_URL |
| Sentry | Error monitoring | 5K events/month | Set SENTRY_DSN |
| Neon / Render PostgreSQL | Persistent database | 512MB free | Set DATABASE_URL |

See [.env.example](.env.example) for full configuration details.

