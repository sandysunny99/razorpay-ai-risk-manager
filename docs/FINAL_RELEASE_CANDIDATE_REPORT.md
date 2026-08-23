# Final Release Candidate Engineering Report

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026  
**Track**: AI Risk Manager  
**Branch**: `feature/risk-manager-webapp-security`  
**Release Candidate Version**: `2.0.0-rc1`  
**Date**: August 23, 2026  
**Final Release Status**: **RELEASE CANDIDATE FROZEN & FULLY VALIDATED (ALL GATES PASSED)**  

---

## 1. Executive Summary & Quality Gate Status

| Quality Dimension | Verified Status | Evidence |
| :--- | :--- | :--- |
| **Frozen Test Set Immutability** | **PASS (100%)** | SHA-256: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f` |
| **Authoritative Risk Scoring Model** | **PRESERVED** | Deterministic 6-factor composite score ($0-100$). Zero duplicate engines. |
| **Layer 1 Detection Metrics ($T=40$)**| **Recall: $88.06\%$ \| Precision: $100.0\%$** | Intercepts 59 of 67 attacks on frozen test set ($0$ False Positives). |
| **Layer 2 Auto-Action Metrics ($T=75$)**| **Precision: $100.0\%$ \| Recall: $52.24\%$** | $0$ False Positives ($0$ legitimate checkouts interrupted). |
| **Automated Test Suite** | **54 / 54 PASSED ($100\%$)** | Unit, IDOR, Step-Up, Policy, Audit, Encryption, DLP, Cloudflare tests. |
| **Cryptographic Field Protection** | **AES-256-GCM + Versioned KMS** | Nonce uniqueness, authenticated integrity, and key rotation verified. |
| **Data Loss Prevention (DLP)** | **Luhn Scrubber + Secret Scanner** | Proactive regex and Luhn validation across inputs, DB, agent, and logs. |
| **Dynamic Masking Engine** | **Role-Aware Server-Side Masking** | PANs, emails, IPs, phone numbers, customer IDs, and tokens masked. |
| **Cloudflare Security Perimeter** | **Normalized Edge Telemetry** | Ingests WAF actions, Bot scores (1-99 taxonomy), and Ray ID correlation. |
| **Threat Intelligence & Exposure** | **HMAC-SHA-256 PAN Fingerprinting** | Stealer dump and paste leak matching with zero raw PAN exposure. |
| **Frontend SOC Dashboard** | **1,816 Modules ($0$ Errors)** | React 18 + Vite + Tailwind with Security Center and CTI views. |
| **Pre-Deployment Quality Gates** | **100% PASS (`pre_deploy.py`)** | All 7 release criteria automated and validated. |

---

## 2. Verified Empirical Operating Point Metrics ($N = 300$, Held-Out Test Set)

```
                                LAYER 1: BROAD DETECTION (T = 40.0)      LAYER 2: AUTONOMOUS ACTION (T = 75.0)
ACTUAL POSITIVE (Pos=67)        TP = 59              FN = 8              TP = 35              FN = 32 (Score 40-74)
ACTUAL NEGATIVE (Neg=233)       FP = 0               TN = 233            FP = 0               TN = 233
```

- **Layer 1: Broad Risk Detection Operating Point ($T_{\text{detect}} = 40.0$)**:
  - **Recall (Sensitivity)**: **$88.06\%$** ($0.8806$)
  - **Precision**: **$100.00\%$** ($1.0000$, $0$ False Positives)
  - **F1 Score**: **$0.9365$**
  - **Overall Accuracy**: **$97.33\%$**
  - **False Positive Rate (FPR)**: **$0.00\%$**
  - **False Negative Rate (FNR)**: **$11.94\%$**
  - **Illustrative Expected Cost**: **₹40,000** ($(0 \times ₹100) + (8 \times ₹5,000)$)

- **Layer 2: Autonomous Auto-Remediation Operating Point ($T_{\text{action}} = 75.0$)**:
  - **Precision**: **$100.00\%$** ($1.0000$, $0$ False Positives)
  - **Recall**: **$52.24\%$** ($0.5224$)
  - **F1 Score**: **$0.6863$**
  - **Overall Accuracy**: **$89.33\%$**
  - **False Positive Rate (FPR)**: **$0.00\%$**
  - **False Negative Rate (FNR)**: **$47.76\%$** (Sub-critical anomalies routed to Tier 2 Step-Up / Tier 3 Review)
  - **Illustrative Expected Cost**: **₹160,000** ($(0 \times ₹100) + (32 \times ₹5,000)$)

---

## 3. Clear Status Classification & Known Limitations

1. **PCI-Aware Prototype**: Implements PCI-aware architecture and tokenization principles; not an official PCI-DSS Level 1 certification.
2. **Deterministic Risk Scoring**: The Risk Engine calculates composite risk using 6 mathematical factors; the LLM agent investigates and grounds evidence, but **never decides numerical risk**.
3. **Sandbox & Simulation Modes**:
   - **Gateway Adapters**: `MockRazorpayAdapter` and `RazorpayTestAdapter` simulate live vault operations.
   - **Threat Intelligence Provider**: `SyntheticThreatIntelProvider` reproduces stealer dump breach signals safely and offline.
   - **Cloudflare Edge Adapter**: `CloudflareAdapter` normalizes headers and edge signals for local and container deployment.
4. **Illustrative Cost Model**: Cost calculations reflect illustrative evaluation assumptions ($C_{\text{FP}}=₹100, C_{\text{FN}}=₹5,000$).
5. **No Dangerous Actions**: Financial fund transfers are permanently hardcoded to `NEVER_EXECUTE`.

---

## 4. Final Pitch & Submission Declaration

> *"We don't ask an LLM to decide whether money should move.*  
> *The Cloudflare edge filters.*  
> *The risk engine detects.*  
> *The agent investigates.*  
> *The policy engine authorizes.*  
> *The response layer acts progressively.*  
> *The verifier confirms.*  
> *The audit ledger records.*  
> *And our held-out evaluation proves the result."*

**RELEASE CANDIDATE STATUS: FULLY AUDITED, HARDENED, VALIDATED, AND FROZEN FOR SUBMISSION.**
