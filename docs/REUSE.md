# Razorpay Risk Manager Agent: Open-Source Reuse & Adaptation Matrix

## 1. Reference Repository Analysis & Reuse Decisions

In accordance with the hackathon reuse-first principles, 7 open-source repositories were systematically analyzed to inform the architecture:

| Capability | Origin / Reference Repository | License | Strategy | Adaptation / Enhancement Made |
|---|---|---|---|---|
| **Feed Ingestion & Alerting** | `gripebomb/ThreatDeck` | MIT | **ADAPT** | Adapted SHA-256 alert deduplication and JSONPath schema normalization patterns into Python backend. |
| **Card Pattern Detection** | `Weedant/Data-Loss-Prevention` | MIT | **ADAPT & ENHANCE** | Enhanced regex DLP with mathematical **Luhn validation** and **HMAC-SHA256 fingerprinting**. |
| **CTI Threat Model** | `brunoaugusto1978/threatforge` | MIT | **ADAPT** | Adapted entity schemas for `ThreatIndicator`, `ExposureEvent`, `SecurityCase`, and `AuditEvent`. |
| **Threat Intel Provider Pattern** | `pete-builds/mcp-threatintel` | MIT | **ADAPT** | Created decoupled `ThreatIntelProvider` abstract base class with offline high-fidelity `SyntheticProvider`. |
| **Transaction Risk Scoring** | `Dhruvvv-26/AI-Threat-Intelligence-Banking` | MIT | **ADAPT** | Adapted multi-factor transaction anomaly formulas (amount, velocity, geo-IP) into deterministic rule engine. |
| **Dark-Web Architecture** | `osintph/threatintel-platform` | AGPL-3.0 | **REFERENCE ONLY** | Referenced threat source taxonomy without copying code (due to AGPL-3.0 copyleft). |
| **SOC Dashboard Layout** | `thalesgroup-cert/Watcher` | AGPL-3.0 | **REFERENCE ONLY** | Referenced incident investigation queue and filterable alert layouts into modern React + Tailwind UI. |
| **Zero-Knowledge HMAC Fingerprint** | Security Industry Standard | Custom | **BUILD** | Engineered proprietary HMAC-SHA256 card fingerprinting pipeline. |
| **Zombie Token Engine** | Razorpay Problem Specification | Custom | **BUILD** | Built automated scanner to detect active payment tokens on expired/blocked cards. |
| **Policy Guardrail Engine** | Core Security Architecture | Custom | **BUILD** | Built deterministic gatekeeper (`AUTO_EXECUTE`, `REVIEW_REQUIRED`, `NEVER_EXECUTE`). |
| **Agent Orchestrator** | Core Architecture | Custom | **BUILD** | Built lightweight tool-calling agent loop ($10$ steps). |

---

## 2. License Compatibility Guarantee

- **No AGPL Code Copied**: All adapted modules were built using permissive MIT-licensed reference patterns or clean-room implementation.
- **Zero Third-Party Cloud Dependencies**: The system runs entirely self-contained for offline evaluation and instant deployment.
