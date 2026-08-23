# Cloudflare Capability Matrix & Edge Perimeter Architecture

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  
**Status**: Edge Security Perimeter Analysis Complete  

---

## 1. Cloudflare Capabilities & Defense-in-Depth Matrix

| Edge Capability | Plan Tier Requirement | Application Implementation Status | Primary Purpose in Payment Risk Architecture | Fallback / Fail-Safe Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **DNS & Orange-Cloud Proxy** | Free / Pro / Enterprise | **ACTIVE (Simulated / Deployed)** | Hides origin IP (Render/FastAPI); terminates public HTTP traffic at edge. | Direct origin reachability with internal IP whitelisting & HMAC headers. |
| **Edge TLS 1.3 & HSTS** | Free / Pro | **ACTIVE** | Enforces end-to-end encryption in transit; prevents downgrade attacks. | Origin requires TLS 1.2+ minimum. |
| **Cloudflare WAF** | Free (Basic) / Pro (Managed Rules) | **ACTIVE (Logged $\rightarrow$ Enforced)** | Blocks OWASP Top 10, SQLi, XSS, and malicious payloads at edge before reaching FastAPI. | FastAPI Pydantic schema validation & input sanitization. |
| **DDoS Mitigation** | Free / Pro | **ACTIVE (Automatic)** | Layer 3/4 & Layer 7 volumetric flood absorption with zero origin disruption. | FastAPI connection limits and asynchronous event loop concurrency. |
| **Rate Limiting** | Free (Configurable) / Pro | **ACTIVE (Endpoint-Specific)** | Protects sensitive routes (`/risk/investigate`, `/tokens/revoke`, `/step-up/*`). | In-memory token bucket rate limiting on FastAPI gateway. |
| **API Shield & Schema Validation** | Business / Enterprise (Available as OpenAPI) | **ACTIVE (OpenAPI 3.0 Contract)** | Validates incoming JSON bodies against strict `openapi.yaml` contract. | Pydantic v2 strict model parsing and input DLP rejection. |
| **Bot Management & Turnstile** | Free (Turnstile) / Enterprise (Bot Score) | **ACTIVE (Turnstile Integration)** | Detects automated credential stuffing scripts on checkout and login. | Deterministic transaction velocity scoring in `TransactionRiskEngine`. |
| **Ray ID Correlation** | All Plans | **ACTIVE (`CF-Ray` Header Tracking)** | Chained Ray ID in audit ledger for end-to-end request tracing. | Generated UUID `req_id` fallback if Ray ID header is absent. |
| **Security Telemetry Ingestion** | All Plans / Logpush | **ACTIVE (`CloudflareAdapter`)** | Ingests WAF actions, Bot scores, and Rate-limit alerts into agent evidence store. | System logs `CLOUDFLARE_SIGNAL_DEGRADED` and proceeds with internal telemetry. |

---

## 2. Edge-to-Origin Data Flow

```
   INTERNET / CLIENT BROWSER
             │
             ▼
┌──────────────────────────────────────────────┐
│           CLOUDFLARE EDGE PERIMETER          │
│ • DDoS Mitigation & Layer 7 Scrubbing        │
│ • Cloudflare WAF (OWASP Managed Ruleset)     │
│ • Endpoint Rate Limiting (/api/v1/risk/*)    │
│ • API Shield & OpenAPI Schema Validation     │
│ • Turnstile Bot Challenge Verification       │
│ • Generates CF-Ray ID & Security Metadata    │
└──────────────────────┬───────────────────────┘
                       │ HTTPS (TLS 1.3 + Origin Auth)
                       ▼
┌──────────────────────────────────────────────┐
│           FASTAPI ORIGIN GATEWAY             │
│ • Input DLP & Luhn Checksum Scrubber         │
│ • Dynamic Masking Engine (Role-Based)        │
│ • CloudflareAdapter (Normalizes Edge Signals)│
│ • Scopes Request by Tenant (merchant_id)     │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│        DETERMINISTIC ENGINES & AGENT         │
│ • Correlates Edge Signals + Payment Telemetry│
│ • Evaluates Composite Risk (0 - 100)         │
│ • Executes Gated Response (Policy Engine)    │
└──────────────────────────────────────────────┘
```

---

## 3. Fail-Safe Principle

> [!IMPORTANT]
> **Cloudflare is a signal provider, NOT the payment-risk decision maker.**  
> - A Cloudflare WAF alert increases transaction suspicion in the composite risk scorer, but **never automatically revokes gateway payment tokens**.
> - If Cloudflare is unavailable or degraded, the Risk Manager Agent logs `DEGRADED_EDGE_TELEMETRY` and safely evaluates the transaction using internal velocity, device, card lifecycle, and CTI breach signals.
