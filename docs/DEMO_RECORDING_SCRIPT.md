# 2-Minute Demo Video Recording Script & Screenplay

**Target Duration**: 2 minutes (120 seconds)  
**Tools**: Loom, OBS, QuickTime, or Screen Studio  
**Target Resolution**: 1080p (16:9)  
**Starting Screen**: SOC Dashboard (`http://localhost:5173` or `https://razorpay-risk-manager.onrender.com`)

---

## Screenplay & Narration Breakdown

### ⏱ 0:00 – 0:15 | Introduction & Dashboard Overview
- **Visual**: Show the full dark-mode SOC dashboard. Point to the 4 KPI cards with animated count-up numbers and the Global Threat Meter in the header.
- **Narration**:  
  > *"This is the Razorpay AI Risk Manager. It is not a chatbot, and not a static rule engine. It is a closed-loop autonomous security agent that detects compromised credentials, correlates dark-web intelligence, and executes policy-governed token revocations."*

### ⏱ 0:15 – 0:45 | Ingestion & Multi-Factor Anomaly Correlation
- **Visual**: Click the blue button: **"Execute Golden Attack Demo"**. The screen transitions to the Forensic Timeline.
- **Narration**:  
  > *"A ₹18,500 authorization arrives from Moscow. The card was detected in a RedLine Stealer dump 48 hours ago. The vault token is still active, but the physical card expired 3 months ago—a classic zombie token attack. The agent's initial composite risk score reaches 94 out of 100: CRITICAL."*

### ⏱ 0:45 – 1:15 | Policy Guardrails & Autonomous Remediation
- **Visual**: Scroll down the 8-phase stepper to **DECIDE (Policy Guardrail)** and **ACT (Token Revocation)**. Expand the step details.
- **Narration**:  
  > *"Rather than guessing, the agent consults centralized policy guardrails. Under policy PR-01, autonomous token revocation is authorized. Crucially, the AI has a hardcoded NEVER_EXECUTE boundary—it can never transfer funds or alter balances. It calls Razorpay's Vault API to revoke the token in under 200 milliseconds."*

### ⏱ 1:15 – 1:40 | The Closed-Loop Verification & Cryptographic Audit Ledger
- **Visual**: Point to the top banner showing Risk Score drop: **94 → 16 (LOW)**. Click the **"Audit Ledger"** tab to show the SHA-256 block hash.
- **Narration**:  
  > *"This is what makes it truly agentic: the verification loop. The agent queries Razorpay Vault to confirm the token state is REVOKED, and recalculates risk down to 16. It then appends a SHA-256 block to an immutable, tamper-evident audit ledger."*

### ⏱ 1:40 – 2:00 | Real-Time DLP Security & Benchmark Conclusion
- **Visual**: Click the **"SOC & DLP Guard"** tab. Show DLP scanning. Briefly click **"Model Evaluation"** tab showing 100% Precision and 0 False Positives.
- **Narration**:  
  > *"All raw card numbers are protected using zero-knowledge HMAC-SHA-256 fingerprints—raw PANs never touch memory or LLMs. On our frozen 300-record held-out benchmark, the system achieved 100% precision with zero false positives. Thank you."*

---

## Post-Recording Checklist

1. [ ] Upload video to YouTube (Unlisted) or Loom.
2. [ ] Copy video URL.
3. [ ] Add badge to README.md:
   ```markdown
   [![Demo Video](https://img.shields.io/badge/demo-2min%20video-FF0000?logo=youtube)](YOUR_VIDEO_URL)
   ```
