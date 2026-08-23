# Cloudflare Security Perimeter & Edge Architecture

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  

---

## 1. Edge Perimeter Defense-in-Depth

```
  CLIENT / BROWSER / API CONSUMER
                 │
                 ▼
┌──────────────────────────────────────────────┐
│           CLOUDFLARE EDGE PERIMETER          │
│ • Unmetered DDoS Protection (L3/L4 & L7)      │
│ • Cloudflare WAF (OWASP Core Ruleset)        │
│ • Token-Bucket Rate Limiting on API routes   │
│ • API Shield OpenAPI 3.0 Contract Validation │
│ • Turnstile Bot Management                   │
│ • Injects CF-Ray ID, Country, & Bot Score    │
└──────────────────────┬───────────────────────┘
                       │ HTTPS (TLS 1.3 Strict)
                       ▼
┌──────────────────────────────────────────────┐
│           FASTAPI ORIGIN SERVER              │
│ • Input DLP & Luhn Checksum Scrubber         │
│ • CloudflareAdapter (Sanitizes Edge Telemetry)│
│ • Role-Based Dynamic Masking                 │
│ • Authenticated Tenant Scoping (merchant_id) │
└──────────────────────────────────────────────┘
```

---

## 2. Signal Hierarchy & Separation of Powers

1. **Edge Signals are Telemetry**: Cloudflare signals (WAF actions, Bot scores, Rate limits) are normalized into `CloudflareSecurityEvent` and ingested as supporting evidence.
2. **Deterministic Risk Scoring**: The Risk Engine correlates edge signals with internal velocity, token age, and breach intelligence.
3. **Policy Decides Action**: Irreversible gateway actions (token revocation) strictly require policy authorization under Policy Rule `PR-01`.
