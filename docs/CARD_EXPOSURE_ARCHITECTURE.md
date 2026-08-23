# Card Exposure Architecture & Zero-Knowledge Correlation

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  

---

## 1. Zero-Knowledge Card Matching Design

Raw 16-digit PANs are never ingested, stored, matched, or transmitted across the risk management lifecycle.

```
 RAW PAN / PAYMENT TOKEN BOUNDARY
             │
             ▼
┌──────────────────────────────────────────────┐
│       ONE-WAY HMAC-SHA-256 HASHER            │
│  fingerprint = HMAC_SHA256(PAN, server_salt) │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│     CARD EXPOSURE INTELLIGENCE ENGINE        │
│ • Matches against normalized CTI breach feeds│
│ • Evaluates multi-source confidence (0.0-1.0)│
│ • Computes temporal freshness & leak recency │
└──────────────────────┬───────────────────────┘
                       │ EVID-EXP-001 (Exposure Evidence)
                       ▼
┌──────────────────────────────────────────────┐
│      AUTHORITATIVE COMPOSITE RISK ENGINE     │
│ • Exposure weight: 25% of composite score    │
│ • Correlates with Token Lifecycle & Velocity │
└──────────────────────────────────────────────┘
```

---

## 2. Threat Feed Types & Indicator Taxonomy

- **STEALER_LOG**: Malware log extractions (RedLine, Racoon) with 94-98% confidence.
- **DARK_WEB_BREACH**: Forum database dumps with 85-92% confidence.
- **PASTE_LEAK**: Public unverified paste dumps with 30-50% confidence.
- **BIN_CAMPAIGN**: Concentrated fraud clusters across card issuer prefixes.
