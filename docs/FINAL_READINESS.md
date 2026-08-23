# Final Readiness & Hackathon Submission Package

**Hackathon**: Razorpay AI Buildathon 2026  
**Track**: AI Risk Manager  
**Project**: Razorpay Risk Manager Agent  
**Date**: August 23, 2026  
**Submission Status**: FULLY READY & VALIDATED  

---

## 1. Final Quality Gates Checklist

- [x] **Test Set Hash Verified**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f` (100% frozen, 0 modification)
- [x] **45 Passing Backend Automated Tests**: `pytest -v` $\rightarrow$ 45 passed, 0 failed
- [x] **Layer 1 Detection Metrics ($T=40.0$)**: Recall $88.06\%$, Precision $100.0\%$, F1 $0.9365$, FPR $0.0\%$
- [x] **Layer 2 Auto-Action Metrics ($T=75.0$)**: Precision $100.0\%$, Recall $52.24\%$, F1 $0.6863$, FPR $0.0\%$
- [x] **Both Confusion Matrices Rendered**: Detection Matrix ($59/0/233/8$) & Auto-Action Matrix ($35/0/233/32$)
- [x] **Detection Separated from Action**: Strict architectural boundary between discovery and remediation
- [x] **Step-Up 2FA Challenge Modeled**: All 4 states (`SUCCESS`, `FAILED`, `TIMEOUT`, `ABANDONED`) tested
- [x] **Zombie Token Gating**: Dormant tokens require review; zombie + active attack auto-revokes
- [x] **Evidence-Grounded Reasoning**: Structured `[EVID-...]` tags with zero hallucinated signals
- [x] **Dynamic Tool Optimization**: 4 investigation levels (0-3) with explicit skipped tool logging
- [x] **Multi-Tenant IDOR Security**: Merchant data isolation strictly enforced
- [x] **PAN Protection**: HMAC-SHA-256 fingerprinting + regex DLP masking; zero raw PANs in logs/LLM
- [x] **Prompt Injection Defense**: Untrusted threat feeds sanitized and treated as passive data
- [x] **Cryptographic Audit Ledger**: Tamper-evident SHA-256 hash chain with 1-click validator
- [x] **Frontend Production Build**: `npm run build` succeeds with 0 TypeScript errors ($1.8\text{s}$)
- [x] **Documentation Complete**: All evaluation, architecture, and demo runbooks verified

---

## 2. 5-Minute Pitch & Demo Script (Hackathon Presentation)

```
========================================================================================
TIMELINE      SECTION & TOPIC               KEY TALKING POINTS & ACTIONS
========================================================================================
0:00 - 0:30   Problem Statement             "In payments, compromised credentials cause severe losses.
                                             Binary rules create a false dilemma between high fraud
                                             and customer checkout friction."

0:30 - 0:50   Core Architecture             "Our system introduces a Two-Layer Risk Architecture:
                                             - Layer 1: Broad Detection (T=40, 88.06% Recall)
                                             - Layer 2: Autonomous Remediation (T=75, 100% Precision)
                                             - Progressive 5-tier response (Allow, Monitor, 2FA, Review, Revoke)."

0:50 - 1:40   Demo 1: Clean Transaction     In UI: Click 'Scenario 2: Clean Domestic Payment'
                                             Show: Level 0 fast-path, skipped heavy CTI lookups,
                                             instant authorization (ALLOW), 0 ms latency waste.

1:40 - 2:40   Demo 2: Golden Compromise     In UI: Click 'Scenario 1: Stealer Dump + Zombie Token'
                                             Show: Anomaly detected -> Threat feed matched ->
                                             Risk = 94/100 -> Policy PR-01 evaluated ->
                                             Autonomous Vault Revocation -> State Verified ->
                                             Risk Recalculates (94 -> 16) -> Hash chained to audit ledger.

2:40 - 3:30   Demo 3: Step-Up 2FA Challenge  In UI: Click 'Scenario 3: Step-Up 2FA Simulation'
                                             Show: Risk = 54/100 (Tier 2) -> 2FA Challenge issued ->
                                             Customer confirms OTP -> Friction damped ->
                                             Risk drops (54 -> 27) without dropping exposure signals.

3:30 - 4:20   Empirical Evaluation Metrics  In UI: Switch to 'Model Evaluation & Metrics' Tab
                                             Show: Dual Confusion Matrices, Comparative Table,
                                             Ablation Study, and Cost Model (₹160k -> ₹40k reduction).

4:20 - 4:50   Security & Guardrails         In UI: Show Tamper-Evident Audit chain validation,
                                             HMAC-SHA-256 card fingerprinting, DLP masking, and IDOR tests.

4:50 - 5:00   Closing Statement             "We don't ask an LLM to decide whether money moves.
                                             The risk engine detects. The agent investigates.
                                             The policy engine authorizes. The verifier confirms.
                                             And our held-out evaluation proves the result."
========================================================================================
```

---

## 3. Evaluator Q&A Defense Guide

### Q1: Why use two thresholds instead of a single threshold?
> **Answer**: A single threshold forces an impossible compromise: at $T=40$, you achieve $88.06\%$ recall but would cause unacceptable false friction if you revoke tokens automatically; at $T=75$, you achieve $100\%$ precision but miss sub-critical anomalies. Our two-layer architecture uses $T=40$ for broad discovery and non-destructive Step-Up 2FA / SOC review, reserving $T=75$ exclusively for autonomous, irreversible token revocation.

### Q2: Is your overall detector precision 100%?
> **Answer**: At the autonomous action operating point ($T=75.0$), precision is $100.00\%$ ($0$ false positives on $233$ legitimate test records). At the broad detection operating point ($T=40.0$), precision is also $100.00\%$ because all $59$ detected transactions contained legitimate anomaly signals, while catching $88.06\%$ of ground-truth compromises.

### Q3: What happens at intermediate risk scores like 55 or 68?
> **Answer**:
> - At **Risk = 55 (Tier 2: STEP_UP)**: The system initiates a simulated 2FA/OTP challenge. If verified, behavioral friction is damped and risk drops ($54 \rightarrow 27$).
> - At **Risk = 68 (Tier 3: REVIEW)**: The system escalates to SOC Case Management for human supervisor authorization under Policy PG-01 without performing destructive automation.

### Q4: How is sensitive payment card data (PAN) protected?
> **Answer**: Raw PANs, CVVs, and PINs are **never stored, logged, or sent to an LLM**. All dark-web breach feeds and transaction logs are indexed using one-way **HMAC-SHA-256 PAN fingerprints** with Luhn pre-validation. All UI and telemetry logs use masked PANs (`**** **** **** 4921`).

### Q5: Can the LLM agent bypass policy or move money?
> **Answer**: **No.** The LLM operates in an isolated investigation loop (`Agent -> Tool -> Policy -> Executor`). Policy guardrails are hardcoded in deterministic Python. The LLM cannot alter thresholds, cannot authorize financial transfers (`NEVER_EXECUTE`), and cannot revoke tokens outside permitted policy rules.

### Q6: What happens if external services (CTI or LLM) fail?
> **Answer**: The system implements **fail-safe degradation**:
> - If LLM is unavailable: Deterministic scoring and policy guardrails continue uninterrupted.
> - If Threat Intel is unavailable: The agent continues with available internal telemetry (velocity, device, location).
> - If Vault verification fails: Risk remains elevated and a high-priority SOC case is escalated.
