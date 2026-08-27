# Razorpay Risk Manager Agent: Final Project Audit & Delivery Report

**Date**: 2026-08-23T11:37:30+05:30  
**Status**: Ready for Hackathon Evaluation & Demonstration  
**Track**: Razorpay Risk Manager

---

## 1. System Architecture Summary

The **Razorpay Risk Manager Agent** is an agentic payment-risk management platform combining deterministic risk engines, threat intelligence correlation, a tool-calling risk agent, policy guardrails, and cryptographic auditability.

```
+-----------------------------------------------------------------------------+
|                            RAZORPAY SOC DASHBOARD                           |
|      Executive KPIs | 5 Demo Scenarios | Live Timeline | Audit Proof        |
+--------------------------------------┬--------------------------------------+
                                       │ REST API
+--------------------------------------▼--------------------------------------+
|                             FASTAPI RISK GATEWAY                            |
+--------------------------------------┬--------------------------------------+
                                       │
+--------------------------------------▼--------------------------------------+
|                     RISK MANAGER AGENT ORCHESTRATOR                         |
|   1. OBSERVE   2. DETECT       3. INVESTIGATE  4. CORRELATE   5. REASON     |
|   6. ASSESS    7. CHECK POLICY 8. ACT          9. VERIFY     10. AUDIT      |
+--------┬─────────────────────────────┬──────────────────────────────┬-------+
         │                             │                              │
+--------▼-----------+      +----------▼----------+      +------------▼-------+
| DETERMINISTIC      |      | THREAT INTEL        |      | POLICY GUARDRAILS  |
| ENGINES            |      | PROVIDER            |      | & VERIFICATION     |
| • Txn Risk (25%)   |      | • SyntheticProvider |      | • AUTO_EXECUTE     |
| • Exposure (25%)   |      |   (9 Test Profiles) |      | • REVIEW_REQUIRED  |
| • Card Risk (15%)  |      | • Stealer Logs      |      | • NEVER_EXECUTE    |
| • Token/Zombie     |      | • Paste Dumps       |      | • Recalculate Risk |
|   Risk (15%)       |      | • Zero-Knowledge    |      |   (94 -> 21)       |
| • Customer (10%)   |      |   HMAC-SHA-256      |      | • Tamper-Evident   |
| • Merchant (10%)   |      |   Fingerprints      |      |   Hash Ledger      |
+--------------------+      +---------------------+      +--------------------+
```

---

## 2. What Was Verified & Hardened

1. **Deterministic Risk Engines**: Verified all 6 scoring components, threshold boundaries ($0, 25, 50, 75, 94, 100$), and weight normalization.
2. **Zombie Token Detection**: Verified detection of active tokens on expired, blocked, or replaced cards.
3. **Card Security & DLP**: Verified Luhn validation, HMAC-SHA-256 card fingerprinting, and regex masking across all logs and payloads.
4. **Policy Guardrail Engine**: Enforced `AUTO_EXECUTE`, `REVIEW_REQUIRED`, and `NEVER_EXECUTE` gates with structured `PolicyDecision` objects.
5. **Action & Verification**: Hardened the `ACT → VERIFY → RECALCULATE` loop to verify gateway state transition before dropping risk score ($94 \rightarrow 21$).
6. **Tamper-Evident Hash Chain Audit Log**: Hardened `AuditEvent` with SHA-256 hash chaining (`current_hash = SHA256(data + previous_hash)`) and automated chain validation tooling (`verify_audit_chain()`).
7. **Adversarial & Prompt Injection Defense**: Verified that external CTI data is strictly treated as data schemas and never placed in raw LLM system prompt instructions.
8. **Multi-Scenario Demo Controller**: Built 5 one-click scenario triggers (Golden Attack, Policy Denial, Prompt Injection Defense, Zombie Token Scan, Clean Domestic Transaction).

---

## 3. What Was Reused, Adapted, and Newly Built

| Origin | Nature | Components Involved |
|---|---|---|
| **`gripebomb/ThreatDeck`** | Architectural Adaptation | Alert deduplication & schema normalization patterns |
| **`Weedant/Data-Loss-Prevention`** | Pattern Adaptation & Enhancement | PAN regex candidate scrubber + mathematical Luhn check + HMAC-SHA-256 |
| **`brunoaugusto1978/threatforge`** | Data Model Adaptation | CTI entity relationships & case management schemas |
| **`Dhruvvv-26/AI-Threat-Intelligence-Banking`** | Heuristic Adaptation | Multi-factor transaction anomaly formulas (amount, velocity, geo) |
| **`pete-builds/mcp-threatintel`** | Pattern Adaptation | Decoupled `ThreatIntelProvider` abstract base class |
| **`osintph/threatintel-platform`** | Architectural Reference (0% code) | Threat feed taxonomy |
| **`thalesgroup-cert/Watcher`** | Architectural Reference (0% code) | SOC incident investigation layout |
| **Proprietary Built** | Newly Built | Agent Tool Orchestrator loop, Zombie Token Engine, Policy Guardrail Engine, Verification Engine, Tamper-Evident Hash Chain Audit Engine, React SOC UI |

---

## 4. Test & Build Results

- **Automated Backend Pytest Suites**: **21 / 21 passed** in $1.99\text{s}$
  - `test_adversarial_threat.py` (3 tests passed)
  - `test_audit_chain.py` (3 tests passed)
  - `test_e2e_agent.py` (1 test passed)
  - `test_policy.py` (4 tests passed)
  - `test_risk_engines.py` (4 tests passed)
  - `test_security.py` (6 tests passed)
- **Frontend Production Build**: **1,812 modules transformed, 0 TypeScript errors** in $4.77\text{s}$

---

## 5. Hackathon Final Demo Sequence (3 Minutes)

| Time | Phase | Screen Action | Narrative & Key Takeaway |
|---|---|---|---|
| **0:00 - 0:20** | **Problem Statement** | Dashboard Header | Explain the rise of infostealer logs weaponized against active payment tokens & zombie tokens. |
| **0:20 - 0:40** | **SOC Overview** | Executive Metrics & Zombie Panel | Highlight active zombie token `tok_zombie_999` on expired card `**** 8820`. |
| **0:40 - 1:20** | **Golden Attack Execution** | Click *"Execute Golden Attack Demo"* | Ingests ₹18,500 payment from Moscow on card `**** 4921`. Zero-knowledge HMAC match on RedLine Stealer dump. Risk = 94 (`CRITICAL`). |
| **1:20 - 1:50** | **Policy & Remediation** | Investigation Timeline | Policy permits Token Revocation (`AUTO_EXECUTE`) but blocks Card Suspension (`REVIEW_REQUIRED`). Agent revokes token on Razorpay vault. |
| **1:50 - 2:20** | **Verification & Recalculation**| Timeline Recalculation Node | System queries gateway vault $\rightarrow$ confirmed `REVOKED` $\rightarrow$ **Risk drops from 94 to 21 (`LOW`)**. |
| **2:20 - 2:45** | **Tamper-Evident Audit Proof** | Tamper-Evident Audit Tab | Click *"Verify Hash Chain Integrity"* $\rightarrow$ Live cryptographic proof verifies all chained blocks are tamper-free. |
| **2:45 - 3:00** | **Conclusion** | Security Cases Tab | Show generated incident case dispatched to SOC Tier 2. Conclude with Razorpay ecosystem alignment. |
