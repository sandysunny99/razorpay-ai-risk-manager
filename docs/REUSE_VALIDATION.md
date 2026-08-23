# Reference Repository Reuse & Adaptation Validation

**Date**: 2026-08-23T11:36:30+05:30  
**Status**: Formal Audit & Attribution Review

---

## 1. Grounded Reuse & Attribution Matrix

| Repository | License | Nature of Relationship | Copied Code? | Concept / Architectural Pattern Adapted |
|---|---|---|---|---|
| **`osintph/threatintel-platform`** | AGPL-3.0 | **Architectural Reference** | **NO (0% copied)** | Referenced dark-web threat feed normalization schema and IOC taxonomy. No code copied due to AGPL copyleft restrictions. |
| **`gripebomb/ThreatDeck`** | MIT | **Architectural Adaptation** | **NO (Clean Python build)** | Adapted the SHA-256 content deduplication mechanism and multi-tier alerting classification patterns into Python async engines. |
| **`thalesgroup-cert/Watcher`** | AGPL-3.0 | **Architectural Reference** | **NO (0% copied)** | Referenced SOC incident investigation layout and filterable alert inventory concepts for modern React UI. |
| **`brunoaugusto1978/threatforge`** | MIT | **Data Model Adaptation** | **NO (Clean Python build)** | Adapted relational schemas for `ThreatIndicator`, `ExposureEvent`, `SecurityCase`, and `AuditEvent`. |
| **`Dhruvvv-26/AI-Threat-Intelligence-Banking`** | MIT | **Heuristic Adaptation** | **NO (Clean Python build)** | Adapted multi-factor transaction anomaly formulas (amount deviation, velocity window, geo-IP mismatch). |
| **`Weedant/Data-Loss-Prevention`** | MIT | **Pattern Adaptation & Enhancement** | **NO (Enhanced build)** | Adapted PAN candidate regex pattern; enhanced with mathematical **Luhn checksum validation** and **HMAC-SHA-256 PAN fingerprinting**. |
| **`pete-builds/mcp-threatintel`** | MIT | **Pattern Adaptation** | **NO (Clean Python build)** | Adapted pluggable provider abstraction (`ThreatIntelProvider` ABC) to decouple feed ingestion from risk correlation. |

---

## 2. IP & License Integrity Declaration

1. **Zero Copied Proprietary/GPL Source**: All backend algorithms (Luhn, HMAC fingerprinting, composite scoring, policy evaluation, hash-chained ledger) were written as clean-room implementations in Python/FastAPI.
2. **Zero Third-Party Cloud/API Lock-in**: The system operates 100% self-contained for offline hackathon demonstration via `SyntheticThreatIntelProvider` and `MockRazorpayAdapter`.
