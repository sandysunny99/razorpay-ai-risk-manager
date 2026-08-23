# Razorpay AI Risk Manager Agent

<div align="center">

![Razorpay Risk Manager Banner](https://img.shields.io/badge/Razorpay-AI%20Risk%20Manager%20Agent-0D83FF?style=for-the-badge&logo=shield&logoColor=white)
![Build Status](https://img.shields.io/badge/Build-Passing%20(45%20Tests)-10B981?style=for-the-badge)
![Autonomous Precision](https://img.shields.io/badge/Auto--Action%20Precision-100.0%25%20(0%20FP)-6366F1?style=for-the-badge)
![Detection Recall](https://img.shields.io/badge/Detection%20Recall-88.06%25%20(T=40.0)-3B82F6?style=for-the-badge)
![Security Standard](https://img.shields.io/badge/Security-PCI--Aware%20Design%20%7C%20HMAC--SHA--256%20PAN%20Fingerprinting-8B5CF6?style=for-the-badge)
![Hackathon Track](https://img.shields.io/badge/Track-AI%20Risk%20Manager%20(2026)-F59E0B?style=for-the-badge)

**"An explainable, tiered agentic payment-risk orchestration system that detects compromised credentials, verifies threat evidence, calculates multi-factor risk, and executes policy-governed tiered responses with cryptographic auditability."**

</div>

---

## 🎯 Target Single Loss Class & Track Alignment

- **Target Loss Class**: *"Loss caused by compromised payment credentials being used in suspicious transactions."*
- **The Core Problem**: Binary risk rules (e.g. `Risk >= 75 -> BLOCK`, else `PASS`) create a false dilemma between high recall and customer friction.
- **The Two-Layer Solution**:
  - **Layer 1: Broad Risk Detection Layer ($T_{\text{detect}} = 40.0$)**: Intercepts **$92.59\%$ of attack patterns** on validation set ($88.06\%$ on held-out test) with high sensitivity.
  - **Layer 2: Autonomous Auto-Remediation Layer ($T_{\text{action}} = 75.0$)**: Authorizes irreversible token destruction on Razorpay Vault with **$100.0\%$ Precision ($0$ False Positives)**.
  - **Progressive Sub-Critical Defense ($40.0 - 74.9$)**: Routes anomalies to non-destructive Step-Up 2FA Challenge (Tier 2) or SOC Security Review (Tier 3) instead of dropping them.

---

## 📊 Empirical Model & Agent Evaluation (Held-Out Test Set $N = 300$)

| Evaluation Metric | Layer 1: Detection ($T=40.0$) | Layer 2: Auto-Action ($T=75.0$) | Status / Benchmark |
|---|---|---|---|
| **Precision** | **100.00%** ($1.0000$) | **100.00%** ($1.0000$) | **EXCEEDED (0 False Positives)** |
| **Recall (Sensitivity)** | **88.06%** (59 / 67 attacks) | **52.24%** (35 / 67 attacks) | **CALIBRATED DUAL-OPERATING POINTS** |
| **Accuracy** | **97.33%** ($0.9733$) | **89.33%** ($0.8933$) | **HIGH OVERALL ACCURACY** |
| **False Positive Rate (FPR)** | **0.00%** ($0.0000$) | **0.00%** ($0.0000$) | **PERFECT (Zero Legitimate Disruption)** |
| **F1 Score** | **0.9365** | **0.6863** | **BALANCED OPERATING POINTS** |
| **Illustrative Expected Cost** | **₹40,000** | **₹160,000** | **₹120,000 REDUCTION (75% DROP)** |
| **Agent Trajectory Completion** | **100.0%** (100 / 100) | **100.0%** (100 / 100) | **PERFECT** |
| **Dynamic Tool Efficiency** | **4 Levels (0 to 3)** | Fast-path screening on clean | **OPTIMIZED** |
| **Automated Backend Tests** | **45 / 45 Passed** | Unit, IDOR, Step-Up, Policy, Audit | **PASSED** |

---

## 🛡️ The 5 Progressive Response Tiers

```
  Risk Score:  0 -------- 34.9 -------- 39.9 -------- 64.9 -------- 74.9 -------- 100
  Response:     [ Tier 0: LOW ] [ Tier 1: MON ] [ Tier 2: STEP ] [ Tier 3: REV ] [ Tier 4: AUTO ]
  Action:            ALLOW          MONITOR        REQUEST_STEP_UP   SOC REVIEW     REVOKE_TOKEN
  Investigation:    Level 0         Level 1           Level 2          Level 2        Level 3
```

1. **Tier 0: LOW RISK ($0.0 - 34.9$)**: Fast-path authorization (`ALLOW`), skips heavy CTI lookups.
2. **Tier 1: MONITOR ($35.0 - 39.9$)**: Telemetry logging (`MONITOR`) for baseline variance.
3. **Tier 2: STEP_UP ($40.0 - 64.9$)**: Simulated 2FA/OTP challenge (`REQUEST_STEP_UP`) with post-verification risk recalculation ($54 \rightarrow 27$).
4. **Tier 3: REVIEW ($65.0 - 74.9$)**: Security case escalation (`REVIEW_REQUIRED`) for analyst review.
5. **Tier 4: AUTO_REMEDIATE ($\ge 75.0$ or Zombie Token)**: Autonomous token revocation (`AUTO_EXECUTE`) on Razorpay Vault with mandatory state verification.

---

## 🚀 Key Innovations & Capabilities

1. **HMAC-SHA-256 PAN Fingerprinting**: Raw PANs, CVVs, and PINs are **never stored, logged, or sent to an LLM**. Exposure feeds are matched using one-way HMAC-SHA-256 cryptographic fingerprints with Luhn pre-validation.
2. **Deterministic Composite Risk Scoring Engine**: Math-based 6-dimension risk calculation ($25/25/15/15/10/10$) with dynamic factor explanations.
3. **Pluggable Threat Intelligence Abstraction**: Decoupled `ThreatIntelProvider` supporting synthetic threat feeds, dark-web stealer dumps (RedLine/Genesis), and paste monitors.
4. **Policy Guardrail Engine**: The AI Agent never acts unconstrained. Actions are strictly gated:
   - `AUTO_EXECUTE`: Token revocation on critical risk / zombie tokens
   - `REVIEW_REQUIRED`: Card suspension (high customer friction)
   - `NEVER_EXECUTE`: Financial transfers / refunds
5. **Step-Up Verification Challenge Flow**: Simulated 2FA/OTP challenges with mathematical behavioral damping ($0.30\times$), allowing legitimate shoppers to complete checkout while containing fraud across all 4 lifecycle states (`SUCCESS`, `FAILED`, `TIMEOUT`, `ABANDONED`).
6. **Dynamic Tool Selection & Audit Logging**: 4 investigation levels track executed vs. skipped tools with explicit logged reasons in `tool_audit`.
7. **Verified State Transition (`ACT → VERIFY → RECALCULATE`)**: Direct verification loop against Razorpay Vault adapter before dropping risk scores ($94 \rightarrow 16$).
8. **Tamper-Evident Hash-Chained Audit Ledger**: Every agent decision and tool execution is linked with SHA-256 hash chains (`curr_hash = SHA256(data + prev_hash)`), verifiable in 1-click on the dashboard.
9. **SOC Security Dashboard**: High-fidelity React dashboard with dual confusion matrices, two-layer architecture metrics, tier distributions, live risk stream, and cryptographic audit validation.

---

## 🏗️ Architecture Summary

```
                         USER / MERCHANT / WEBHOOK
                                    │
                                    ▼
                         FASTAPI RISK GATEWAY
                                    │
                       DYNAMIC RISK MANAGER AGENT
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
 DETERMINISTIC ENGINES       THREAT INTELLIGENCE        POLICY GUARDRAILS
 • Transaction Risk           • Synthetic Provider       • Tier 0: ALLOW
 • Card Risk (Expiration)     • Stealer Logs (RedLine)   • Tier 1: MONITOR
 • Token Risk & Zombie Token  • Dark-Web Pastes          • Tier 2: REQUEST_STEP_UP
 • Exposure Correlation       • BIN Intelligence         • Tier 3: REVIEW_REQUIRED
       └────────────────────────────┬────────────────────• Tier 4: AUTO_EXECUTE
                                    │
                       COMPOSITE RISK (0 - 100)
                                    │
                         TIERED DEFENSIVE RESPONSE
                       • Low/Mon: Fast-path / Telemetry
                       • Step-Up: 2FA Challenge & Recalculation
                       • Critical: Revoke Token on Razorpay Vault
                       • Verify: Vault Query State Check
                       • Audit: Tamper-Evident Hash Record
```

---

## ⚡ Quickstart & Local Deployment

### 1. Verify Held-Out Test Set Hash (Integrity Gate)
```powershell
python scripts/verify_test_set.py
```

### 2. Run Automated Pytest Suite (45 Tests)
```powershell
pytest -v
```

### 3. Run Reproducible Evaluation Runner
```powershell
python scripts/run_final_evaluation.py
```

### 4. Backend Service (FastAPI)
```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/`

### 5. Frontend SOC Dashboard (React + Vite + Tailwind)
```powershell
cd frontend
npm install
npm run dev
```
- SOC Dashboard UI: `http://localhost:5173/`

---

## 🎬 1-Click Golden Demo Scenario

In the SOC Dashboard (`http://localhost:5173`), click **"Scenario 1: Stealer Dump + Zombie Token (Golden Path)"**:
1. **Transaction Arrives**: Customer `1042` attempts a ₹18,500 authorization from Moscow (velocity: 4 attempts).
2. **Anomalies Detected**: Amount deviation, Geo mismatch, Velocity spike.
3. **Breach Correlated**: Card fingerprint matched in `Telegram/RedLine-Stealer-Dump-08` ($96\%$ confidence).
4. **Initial Risk**: **94/100 (CRITICAL)** $\rightarrow$ **Tier 4: AUTO_REMEDIATE**.
5. **Policy Evaluated**: Token revocation permitted under Policy `PR-01`.
6. **Autonomous Action**: Agent revokes token `tok_test_123` on Razorpay Vault adapter.
7. **Gateway Verification**: Query confirmed state transition to `REVOKED`.
8. **Risk Recalculated**: Drops **94 → 16 (LOW)**.
9. **Case & Audit**: Security Case `CASE-20260823-...` created and persisted in tamper-evident hash ledger.

---

## 📚 Technical Documentation Index

- [docs/FINAL_RELEASE_TRUTH_MATRIX.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_RELEASE_TRUTH_MATRIX.md) - Final Release Truth & Allowed Claims Matrix (v2.0.0-rc1)
- [docs/FINAL_RELEASE_STATUS.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_RELEASE_STATUS.md) - Final Release Status Specification (v2.0.0-rc1)
- [docs/FINAL_RELEASE_EVIDENCE_MATRIX.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_RELEASE_EVIDENCE_MATRIX.md) - Final Release Evidence Matrix (v2.0.0-rc1)
- [docs/FINAL_SUBMISSION_CHECKLIST.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_SUBMISSION_CHECKLIST.md) - Final Hackathon Submission Checklist & Release Sign-Off
- [docs/LIVE_SECURITY_VERIFICATION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/LIVE_SECURITY_VERIFICATION.md) - Live Security Verification & Data Boundary Inspection Report
- [docs/LIVE_BROWSER_E2E.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/LIVE_BROWSER_E2E.md) - Live Browser End-to-End (E2E) Test & Presentation Walkthrough
- [docs/LIVE_DEPLOYMENT_RESULT.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/LIVE_DEPLOYMENT_RESULT.md) - Live Deployment Result & Public Service Specification
- [docs/DOCKER_VERIFICATION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/DOCKER_VERIFICATION.md) - Docker Containerization & Multi-Stage Image Verification
- [docs/FINAL_RELEASE_V2.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_RELEASE_V2.md) - Final Release Specification (v2.0.0-rc1)
- [docs/FINAL_INTEGRATION_BASELINE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_INTEGRATION_BASELINE.md) - Final Integration Baseline Lock
- [docs/DEPLOYMENT_EVIDENCE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/DEPLOYMENT_EVIDENCE.md) - Deployment Evidence & Verification Record
- [docs/LIVE_SECURITY_EVIDENCE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/LIVE_SECURITY_EVIDENCE.md) - Live Security Evidence & Control Evaluation Record
- [docs/FINAL_RELEASE_CANDIDATE_REPORT.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_RELEASE_CANDIDATE_REPORT.md) - Final Release Candidate Engineering Report
- [docs/FINAL_IMPLEMENTATION_REPORT.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_IMPLEMENTATION_REPORT.md) - Final Implementation & Security Engineering Report
- [docs/SECURITY_EVIDENCE_MATRIX.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/SECURITY_EVIDENCE_MATRIX.md) - Security Evidence & Control Verification Matrix
- [docs/FINAL_WEBAPP_READINESS.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_WEBAPP_READINESS.md) - Final Web Application Readiness & Deployment Verification
- [docs/IMPLEMENTATION_VERIFICATION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/IMPLEMENTATION_VERIFICATION.md) - Implementation & Code Verification Audit
- [docs/NEXT_PHASE_BASELINE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/NEXT_PHASE_BASELINE.md) - Next Phase Baseline & Current-State Verification
- [docs/FINAL_SYSTEM_ARCHITECTURE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_SYSTEM_ARCHITECTURE.md) - Final System Architecture & Defense-in-Depth Specification
- [docs/CLOUDFLARE_SECURITY_ARCHITECTURE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/CLOUDFLARE_SECURITY_ARCHITECTURE.md) - Cloudflare Security Perimeter & Edge Architecture
- [docs/CARD_EXPOSURE_ARCHITECTURE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/CARD_EXPOSURE_ARCHITECTURE.md) - Card Exposure Architecture & HMAC Threat Correlation
- [docs/CRYPTOGRAPHIC_DATA_PROTECTION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/CRYPTOGRAPHIC_DATA_PROTECTION.md) - Cryptographic Data Protection & Key Management
- [docs/DATA_CLASSIFICATION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/DATA_CLASSIFICATION.md) - Data Classification Policy & Sensitivity Taxonomy
- [docs/DATA_FLOW_SECURITY_MAP.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/DATA_FLOW_SECURITY_MAP.md) - End-to-End Data Flow Security Map
- [docs/DATA_RETENTION_POLICY.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/DATA_RETENTION_POLICY.md) - Data Retention Policy & Secure Lifecycle Management
- [docs/POST_DEPLOYMENT_SMOKE_TEST.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/POST_DEPLOYMENT_SMOKE_TEST.md) - Post-Deployment Verification & Smoke Test Runbook
- [docs/RELEASE_CANDIDATE_AUDIT.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/RELEASE_CANDIDATE_AUDIT.md) - Release Candidate Audit & Final Submission Declaration
- [docs/RELEASE_BASELINE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/RELEASE_BASELINE.md) - Release baseline execution & metric reproduction
- [docs/PRE_RELEASE_AUDIT.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/PRE_RELEASE_AUDIT.md) - Pre-release architecture & codebase audit report
- [docs/FINAL_READINESS.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_READINESS.md) - Final submission checklist, 5-minute pitch script & evaluator Q&A
- [docs/FINAL_EVALUATION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_EVALUATION.md) - Comprehensive final evaluation report & metric breakdown
- [docs/FINAL_BASELINE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/FINAL_BASELINE.md) - Exact baseline reproduction & frozen test set checksum
- [docs/BEFORE_AFTER_TIERED_RISK.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/BEFORE_AFTER_TIERED_RISK.md) - Two-layer risk architecture & before/after comparison
- [docs/STEP_UP_FLOW.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/STEP_UP_FLOW.md) - Step-Up 2FA challenge flow & mathematical recalculation mechanics
- [docs/AGENT_INVESTIGATION_LEVELS.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/AGENT_INVESTIGATION_LEVELS.md) - 4 investigation levels & dynamic tool selection matrix
- [docs/VALIDATION_THRESHOLD_SELECTION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/VALIDATION_THRESHOLD_SELECTION.md) - Empirical validation threshold sweep justification
- [docs/MODEL_EVALUATION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/MODEL_EVALUATION.md) - Empirical metrics, confusion matrix, ablation study & threshold curve
- [docs/AGENT_EVALUATION.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/AGENT_EVALUATION.md) - 100-scenario automated agent benchmark & calibrated reasoning
- [docs/DATASET.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/DATASET.md) - Evaluation dataset methodology, schema & synthetic generation
- [docs/DEMO_RUNBOOK.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/DEMO_RUNBOOK.md) - Step-by-step live demo presentation runbook
- [docs/ARCHITECTURE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/ARCHITECTURE.md) - System architecture, data flow & modular design
- [docs/SECURITY.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/docs/SECURITY.md) - Cryptographic boundary, HMAC fingerprinting, DLP & threat sanitization
- [REUSE.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/REUSE.md) - Reference repository analysis & reuse matrix
- [HACKATHON_DEMO.md](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/HACKATHON_DEMO.md) - End-to-end demo walkthrough guide
