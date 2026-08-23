# Razorpay AI Risk Manager Agent: Final Release Specification (v2.0.0-rc1)

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026  
**Track**: AI Risk Manager  
**Branch**: `feature/risk-manager-webapp-security`  
**Release Version**: `v2.0.0-rc1`  
**Date**: August 23, 2026  
**Final Release Lifecycle Status**: **READY_FOR_SUBMISSION**  

---

## 1. Frozen Baseline & Verified Empirical Metrics

The held-out evaluation dataset is frozen and immutable:

- **Held-Out Test Set**: `evaluation/test.jsonl` ($N = 300$, 67 Positive, 233 Negative)
- **SHA-256 Checksum**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`
- **Integrity Status**: **PASS (Zero Mutation, Zero Data Leakage)**

```
                                LAYER 1: BROAD DETECTION (T = 40.0)      LAYER 2: AUTONOMOUS ACTION (T = 75.0)
ACTUAL POSITIVE (Pos=67)        TP = 59              FN = 8              TP = 35              FN = 32 (Score 40-74)
ACTUAL NEGATIVE (Neg=233)       FP = 0               TN = 233            FP = 0               TN = 233
```

| Metric Dimension | Layer 1: Broad Detection ($T=40.0$) | Layer 2: Auto-Action ($T=75.0$) | Operational Guarantee |
| :--- | :--- | :--- | :--- |
| **Precision** | **100.00%** ($1.0000$) | **100.00%** ($1.0000$) | Zero false positives across both operating points |
| **Recall (Sensitivity)** | **88.06%** (59 / 67 attacks) | **52.24%** (35 / 67 attacks) | Layer 1 intercepts 24 additional attack vectors |
| **F1 Score** | **0.9365** | **0.6863** | High composite balance |
| **False Positive Rate** | **0.00%** ($0.0000$) | **0.00%** ($0.0000$) | Zero friction on legitimate customer checkouts |
| **Illustrative Expected Cost** | **₹40,000** | **₹160,000** | **₹120,000 illustrative liability reduction ($75\%$ drop)** |

---

## 2. Comprehensive Subsystem Architecture

1. **Deterministic Payment Risk Kernel**:
   - 6-factor composite mathematical scoring ($0-100$ scale).
   - Evaluates velocity ($25\%$), threat exposure ($25\%$), token age/lifecycle ($15\%$), geo-distance ($15\%$), customer history ($10\%$), and merchant risk profile ($10\%$).
   - The LLM agent **never calculates risk scores**; scoring is strictly deterministic.

2. **Policy Guardrail Engine & 5-Tier Response**:
   - Centralized boundary governance:
     - **Tier 0: ALLOW** (Score $< 20$)
     - **Tier 1: MONITOR** (Score $20-39$)
     - **Tier 2: STEP_UP 2FA** (Score $40-59$)
     - **Tier 3: SOC REVIEW** (Score $60-74$)
     - **Tier 4: AUTO_REMEDIATE** (Score $\ge 75$)
   - Irreversible actions strictly require Policy `PR-01` authorization.

3. **Cloudflare Security Perimeter Adapter**:
   - Ingests and normalizes edge WAF actions, Bot scores (1-99 taxonomy: `LIKELY_AUTOMATED`, `LIKELY_HUMAN`, `VERIFIED_BOT`), Rate limits, and CF-Ray tracing.
   - Strips cookies and authorization headers before storing telemetry.

4. **Data Protection, Encryption & Key Management**:
   - **AES-256-GCM** authenticated field encryption with unique 96-bit nonces.
   - Versioned `EnvironmentKeyProvider` (`v1`, `v2`) with rotation and zero raw key leakage in metadata.
   - Proactive multi-pattern DLP with Luhn PAN candidate verification and secrets scrubber.
   - Role-aware dynamic masking across backend API serializers.

5. **Threat Intelligence & Card Exposure Platform**:
   - Privacy-preserving HMAC-SHA-256 fingerprint matching against synthetic stealer dumps and dark web paste feeds.
   - Zero raw PAN stored, accepted, or transmitted.

6. **React SOC Dashboard & Security Center**:
   - 14 integrated operational views including live Security Center, Data Protection matrix, Interactive DLP sandbox, Threat Intel CTI overview, and Dual-Threshold Evaluation dashboard.

---

## 3. Verified Quality Gates & Test Results

- **Backend Pytest Suite**: **54 / 54 PASSED** in $1.86\text{s}$ (`pytest -q`).
- **Pre-Deployment Runner**: **100% PASS** (`python scripts/pre_deploy.py`).
- **Frontend Production Build**: **1,816 modules transformed with 0 TypeScript errors** in $1.15\text{s}$ (`npm run build`).

---

## 4. Operational Classification & Known Limitations

- **PCI-Aware Prototype**: Implements PCI-aware architecture and tokenization principles; not an official PCI-DSS Level 1 certification.
- **Threat Intelligence Feeds**: `SyntheticThreatIntelProvider` reproduces stealer dump breach signals safely and offline for reproducible evaluation.
- **Gateway & Edge Adapters**: `MockRazorpayAdapter`, `RazorpayTestAdapter`, and `CloudflareAdapter` simulate gateway actions and edge telemetry safely in sandbox/demo modes.
- **Cost Model**: Reflects illustrative evaluation assumptions ($C_{\text{FP}}=₹100, C_{\text{FN}}=₹5,000$).

---

## 5. Final Pitch & Submission Declaration

> *"We don't ask an LLM to decide whether money should move.*  
> *The Cloudflare edge filters.*  
> *The risk engine detects.*  
> *The agent investigates.*  
> *The policy engine authorizes.*  
> *The response layer acts progressively.*  
> *The verifier confirms.*  
> *The audit ledger records.*  
> *And our held-out evaluation proves the result."*

**STATUS: RELEASE CANDIDATE v2.0.0-rc1 IS FROZEN AND READY FOR SUBMISSION.**
