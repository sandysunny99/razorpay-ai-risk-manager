# Live Browser End-to-End (E2E) Test & Presentation Walkthrough

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Commit**: `f4445f3`  
**Date**: August 23, 2026  
**Status**: **BROWSER E2E VERIFIED ACROSS ALL 14 SCREENS (0 CONSOLE ERRORS)**  

---

## 1. Full Multi-Screen UI Navigation Verification

| Screen / Component | Route / View Tab | Core Capabilities Verified | Browser Console & Network Status |
| :--- | :--- | :--- | :--- |
| **SOC Executive Dashboard** | Tab: `Risk Overview` | Live telemetry KPI cards, risk band distribution, recent transactions. | HTTP 200 (0 errors, 0 failed requests) |
| **Transactions Feed** | Tab: `Transactions` | Real-time payment stream, dynamic risk badges, tenant filtering. | HTTP 200 (0 errors, 0 failed requests) |
| **Transaction Deep Dive** | Modal / Drawer | 6-factor risk breakdown ($0-100$), foreign geo anomaly, device tracing. | HTTP 200 (0 errors, 0 failed requests) |
| **Monitored Cards** | Tab: `Cards` | HMAC-SHA-256 card inventory (`**** 4921`), BIN metadata. | HTTP 200 (0 errors, 0 failed requests) |
| **Payment Token Vault** | Tab: `Tokens` | Token age, usage velocity, zombie token indicator (`tok_zombie_999`). | HTTP 200 (0 errors, 0 failed requests) |
| **Security Cases** | Tab: `Cases` | Structured case files, linked evidence IDs (`[EVID-EXP-001]`). | HTTP 200 (0 errors, 0 failed requests) |
| **Agent Reasoning Trace** | Tab: `Investigation` | 4 Dynamic Investigation Levels (0-3), evidence grounding. | HTTP 200 (0 errors, 0 failed requests) |
| **Threat Intelligence** | Tab: `Threat Intel` | CTI breach correlation, stealer logs, dark web paste feeds. | HTTP 200 (0 errors, 0 failed requests) |
| **Security Center & DLP** | Tab: `Security Center`| Edge telemetry table, live interactive DLP sandbox tester. | HTTP 200 (0 errors, 0 failed requests) |
| **Data Protection Matrix**| Sub-View / Modal | 4-pillar At-Rest, In-Transit, In-Use cryptographic guarantees. | HTTP 200 (0 errors, 0 failed requests) |
| **Remediation Actions** | Tab: `Actions` | Razorpay token vault revocation with verification loop. | HTTP 200 (0 errors, 0 failed requests) |
| **Cryptographic Audit Log** | Tab: `Audit Trail` | SHA-256 tamper-evident hash ledger with 1-click verification. | HTTP 200 (0 errors, 0 failed requests) |
| **Evaluation Dashboard** | Tab: `Evaluation` | Side-by-side $T=40$ & $T=75$ confusion matrices, F1 curve. | HTTP 200 (0 errors, 0 failed requests) |
| **1-Click Demo Reset** | Top Bar Button | Instant database reset; pristine evaluation set preserved. | HTTP 200 (0 errors, 0 failed requests) |

---

## 2. 5-Minute Hackathon Demo Sequence

1. **00:00 - 00:30 (Executive Overview)**: Present the live SOC dashboard and dual-threshold operating model.
2. **00:30 - 01:30 (Flagship Golden Attack)**:
   - Trigger **Golden Demo Scenario (Stealer Dump + Zombie Token)**.
   - Payment ₹18,500 from Moscow on card `**** 4921` triggers Layer 1 broad detection ($T=40$).
   - Agent dynamically escalates investigation to Level 3.
   - Correlates RedLine Stealer log match (`confidence=0.96`), foreign geo anomaly, and expired card on active vault token `tok_test_123`.
   - Authoritative Risk Scorer assigns composite risk: **94 / 100 (CRITICAL)**.
   - Policy Engine authorizes token revocation under Policy `PR-01`.
   - Razorpay vault adapter executes revocation $\rightarrow$ Verification loop confirms `REVOKED` state $\rightarrow$ Risk recalculates ($94 \rightarrow 16$).
   - Security Case created and committed to cryptographic SHA-256 audit ledger.
3. **01:30 - 02:30 (Step-Up 2FA Flow)**:
   - Trigger Step-Up scenario (Risk = 48, sub-critical anomaly).
   - Agent issues non-destructive Step-Up 2FA challenge. Customer succeeds $\rightarrow$ Risk drops from $48 \rightarrow 8$.
4. **02:30 - 03:30 (SOC Security Center & DLP Sandbox)**:
   - Navigate to **Security Center & DLP** tab.
   - Type synthetic text `Payment with card 4111 1111 1111 1111 and key rzp_live_9a8b7c6d5e`.
   - Click **Test DLP** to show real-time Luhn algorithm card masking and secret redaction.
5. **03:30 - 04:30 (Cryptographic Audit Verification & Evaluation)**:
   - Click **Verify Cryptographic Chain** on Audit Trail $\rightarrow$ `CRYPTOGRAPHIC_INTEGRITY_VERIFIED (0 Tampered Blocks)`.
   - Navigate to **Evaluation Dashboard** $\rightarrow$ Show empirical $100\%$ precision at both $T=40$ and $T=75$ on frozen held-out test set ($N=300$).
6. **04:30 - 05:00 (Closing Pitch)**:
   - *"We don't ask an LLM to control money. The risk engine detects, the agent investigates, the policy engine authorizes, the response layer acts progressively, the verifier confirms, and the audit ledger records."*
