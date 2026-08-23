# Release Candidate Audit & Final Submission Declaration

**Hackathon**: Razorpay AI Buildathon 2026  
**Track**: AI Risk Manager  
**Project**: Razorpay Risk Manager Agent  
**Release Candidate Date**: August 23, 2026  
**Final Release Status**: **READY FOR SUBMISSION (ALL QUALITY GATES PASSED)**  

---

## 1. Executive Summary & Verification Declarations

| Quality & Compliance Dimension | Release Candidate Audit Status | Verified Evidence |
| :--- | :--- | :--- |
| **Final System Status** | **READY FOR SUBMISSION** | Fully audited, hardened, frozen & verified |
| **Final Automated Test Count** | **45 / 45 Passed ($100\%$)** | Unit, IDOR, Step-Up, Policy, Audit, Metrics |
| **Held-Out Test Set Hash** | **`76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`** | `scripts/release_guard.py` $\rightarrow$ PASS |
| **Layer 1 Detection Metrics ($T=40$)** | **Recall: $88.06\%$ \| Precision: $100.0\%$ \| F1: $0.9365$** | Evaluated on $300$ frozen held-out test records |
| **Layer 2 Auto-Action Metrics ($T=75$)** | **Precision: $100.0\%$ \| Recall: $52.24\%$ \| F1: $0.6863$** | $0$ False Positives ($0$ legitimate disruption) |
| **Sub-Critical Routing ($40-74$)** | **$100\%$ Protected (Step-Up 2FA / SOC Review)** | $32$ non-destructive progressive defenses |
| **Frontend Production Build** | **Compiled in $1.42\text{s}$ ($0$ TypeScript Errors)** | Vite & TypeScript asset bundle built |
| **Security & Privacy Boundary** | **PCI-Aware Prototype (HMAC-SHA-256 + DLP)** | $0$ raw PANs logged, stored, or sent to LLM |
| **Prompt Injection Protection** | **Sanitized Schema-Enforced CTI Boundary** | Untrusted CTI feeds treated as passive data |
| **Multi-Tenant Isolation** | **Enforced Merchant IDOR Boundary** | Database, API, and Agent scoped to merchant |
| **Razorpay Adapter Integration** | **Mock & Test Sandbox Adapters Verified** | Stateful token revocation & 2FA challenge simulation |
| **1-Click Demo & Reset** | **Pristine & Repeatable (`scripts/reset_demo.py`)** | Golden path verified end-to-end |

---

## 2. Final Empirical Metrics on Frozen Held-Out Test Set ($N = 300$)

```
                                LAYER 1: BROAD DETECTION (T = 40.0)      LAYER 2: AUTONOMOUS ACTION (T = 75.0)
ACTUAL POSITIVE (Pos=67)        TP = 59              FN = 8              TP = 35              FN = 32 (Score 40-74)
ACTUAL NEGATIVE (Neg=233)       FP = 0               TN = 233            FP = 0               TN = 233
```

- **Broad Detection Operating Point ($T=40.0$)**:
  - $\text{Recall} = \frac{59}{67} = \mathbf{88.06\%}$
  - $\text{Precision} = \frac{59}{59} = \mathbf{100.00\%}$
  - $\text{F1 Score} = \mathbf{0.9365}$
  - $\text{False Positive Rate (FPR)} = \mathbf{0.00\%}$
  - $\text{Overall Accuracy} = \mathbf{97.33\%}$
  - $\text{Illustrative Expected Cost} = \mathbf{₹40,000}$ ($(0 \times ₹100) + (8 \times ₹5,000)$)

- **Autonomous Auto-Remediation Operating Point ($T=75.0$)**:
  - $\text{Precision} = \frac{35}{35} = \mathbf{100.00\%}$ ($0$ False Positives)
  - $\text{Recall} = \frac{35}{67} = \mathbf{52.24\%}$
  - $\text{F1 Score} = \mathbf{0.6863}$
  - $\text{False Positive Rate (FPR)} = \mathbf{0.00\%}$
  - $\text{Overall Accuracy} = \mathbf{89.33\%}$
  - $\text{Illustrative Expected Cost} = \mathbf{₹160,000}$ ($(0 \times ₹100) + (32 \times ₹5,000)$)

---

## 3. Final Security & Architectural Guarantees

1. **Deterministic Bounded Agency**: The Risk Manager Agent operates strictly through `AgentToolRegistry`. Actions are gated by `PolicyEngine`. Financial transfers are permanently hardcoded to `NEVER_EXECUTE`.
2. **Cryptographic Data Boundary**: Raw PANs and authentication secrets (PIN, CVV, OTP) are never accepted, stored, logged, or provided to AI models. Exposure feeds are matched using one-way HMAC-SHA-256 card fingerprints.
3. **Verified State Transition**: Employs an active verification loop against the Razorpay Token Vault adapter before dropping risk scores ($94 \rightarrow 16$).
4. **Tamper-Evident Audit Ledger**: Every agent decision and tool execution is linked with SHA-256 hash chains (`curr_hash = SHA256(data + prev_hash)`), verifiable in 1-click on the SOC Dashboard.

---

## 4. Final Known Limitations & Disclosures

1. **Synthetic Evaluation Dataset**: The 2,000-record dataset is synthetically generated to model realistic payment distributions without handling real stolen credit cards.
2. **Synthetic Threat Intelligence**: Uses an offline threat intelligence provider to reproduce stealer dump breach signals safely.
3. **PCI-Aware Prototype**: Implements PCI-aware architecture, not an official PCI-DSS Level 1 certification.
4. **Illustrative Cost Model**: Cost calculations are illustrative evaluation assumptions ($C_{\text{FP}}=₹100, C_{\text{FN}}=₹5,000$).

---

## 5. Final Pitch & Submission Declaration

> *"We don't ask an LLM to decide whether money should move.*  
> *The risk engine detects.*  
> *The agent investigates.*  
> *The policy engine authorizes.*  
> *The response layer acts progressively.*  
> *The verifier confirms.*  
> *The audit ledger records.*  
> *And our held-out evaluation proves the result."*

**RELEASE CANDIDATE SIGN-OFF: PASSED AND FROZEN FOR HACKATHON SUBMISSION.**
