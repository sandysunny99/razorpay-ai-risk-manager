# Release Candidate 2 (`v2.0.0-rc2`) Specification

**Release Version**: `v2.0.0-rc2`  
**Verified Commit Hash**: `8666eb4`  
**Release Tag**: `v2.0.0-rc2`  
**Repository**: `sandysunny99/razorpay-ai-risk-manager`  

---

## 1. Release Highlights

Release Candidate 2 (`v2.0.0-rc2`) delivers a fully integrated, enterprise-grade AI Risk Manager web application with:
1. **Dedicated Zombie Card Saver Module**:
   - Disruption-prevention engine that detects stale/expired/blocked cards with active dependent tokens.
   - Calculates merchant recurring revenue impact and customer friction level.
   - Selectively revokes high-risk tokens while preserving legitimate subscription billing.
2. **Real-Time Telemetry & Bounded Threat Enrichment**:
   - Razorpay Test Mode webhooks with raw body HMAC-SHA256 signature verification.
   - Bank Identification Number (BIN) lookup using first 6–8 digits (PCI-DSS compliant).
   - URLhaus malware domain IOC threat intelligence integration.
3. **CI Hardening & Docker Containerization**:
   - 63/63 automated backend pytest test suite passing.
   - Multi-stage Docker container build with static frontend asset serving and health probes.
   - Clean environment-aware API resolution.

---

## 2. Benchmark Baseline Immutability

- **Dataset**: `evaluation/test.jsonl` ($N=300$)
- **SHA-256 Checksum**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`
- **Broad Recall ($T=40.0$)**: **88.06%**
- **Auto-Action Precision ($T=75.0$)**: **100.00% (0 False Positives)**
- **Audit Verification**: 100% Cryptographic Chained Integrity.
