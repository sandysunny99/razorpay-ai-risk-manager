# Final System Architecture & Defense-in-Depth Specification

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  

---

## 1. End-to-End System Architecture Diagram

```
                             INTERNET CLIENTS / BROWSERS
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          CLOUDFLARE EDGE PERIMETER                              │
│ • Cloudflare WAF (OWASP Core Ruleset)      • Layer 3/4 & Layer 7 DDoS Shield    │
│ • Token-Bucket Rate Limiting               • API Shield (OpenAPI 3.0 Contract)  │
│ • Turnstile Bot Management & Bot Scores    • Edge TLS 1.3 Termination & HSTS    │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ HTTPS (Strict Origin Auth)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       FASTAPI SECURITY & ROUTING GATEWAY                        │
│ • Input DLP Gate & Luhn Checksum Scrubber  • Role-Based Dynamic Masking         │
│ • CloudflareAdapter Telemetry Normalizer   • Multi-Tenant Isolation (merchant) │
│ • AES-256-GCM Field Encryption Engine      • Versioned KMS Key Provider         │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   DETERMINISTIC PAYMENT-RISK SCORING KERNEL                     │
│ • Transaction Velocity (25%)               • Card Exposure Correlation (25%)    │
│ • Token Lifecycle & Zombie State (15%)     • Foreign Geo / IP Distance (15%)    │
│ • Customer Chargeback History (10%)        • Merchant Risk Profile (10%)        │
│ ──► Layer 1 Broad Detection (T = 40.0) ──► Layer 2 Auto-Remediation (T = 75.0)  │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       TIERED RISK MANAGER AGENT & TOOLS                         │
│ • Dynamic Investigation Levels (0 - 3)     • Calibrated Structured Reasoning    │
│ • Policy Engine Guardrails (PR-01 - PR-05) • Non-Destructive Step-Up 2FA Challenge│
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                  RESTORATION, VERIFICATION & AUDIT SUB-SYSTEMS                  │
│ • Razorpay Token Vault Adapter             • State Transition Verification      │
│ • Risk Recalculation Engine (94 ──► 16)    • SHA-256 Chained Hash Audit Ledger  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Guarantees

1. **Separation of Concerns**: Threat Intelligence and Cloudflare edge signals provide telemetry; the deterministic Risk Scorer calculates composite risk; the Policy Engine gates actions.
2. **Zero-Knowledge Matching**: Card numbers are never stored in plaintext. HMAC-SHA-256 fingerprints enable zero-knowledge correlation against external breach dumps.
3. **Defense-in-Depth DLP**: Proactive regex and Luhn algorithm scanners operate across API inputs, database writes, agent reasoning traces, log pipelines, and frontend JSON responses.
