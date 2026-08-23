# Web Application Architecture Specification (v2.0.0-rc1)

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Architecture Style**: Integrated Defense-in-Depth Layered Architecture  

---

## 1. End-to-End Control & Data Flow

```
                                 INTERNET
                                    │
                                    ▼
                     CLOUDFLARE EDGE PERIMETER
             ┌────────────────────────────────────────┐
             │ • TLS 1.3 / Strict HTTPS Termination   │
             │ • Managed WAF & Bot Management (1–99)  │
             │ • Rate Limiting & CF-Ray Request ID    │
             └──────────────────┬─────────────────────┘
                                │ Injected Headers
                                ▼
                     FASTAPI GATEWAY ENGINE
             ┌────────────────────────────────────────┐
             │ • JWT Authentication & RBAC            │
             │ • Multi-Tenant IDOR Scope Enforcement  │
             │ • Real-time DLP Luhn Input Scrubber    │
             └──────────────────┬─────────────────────┘
                                │ Sanitized Payload
                                ▼
                     DETERMINISTIC RISK SCORER
             ┌────────────────────────────────────────┐
             │ • Multi-Factor Mathematical Fusion      │
             │ • Layer 1 Detection (Threshold T=40.0) │
             │ • Layer 2 Auto-Action (Threshold T=75.0│
             └──────────────────┬─────────────────────┘
                                │ Risk Score & Factors
                                ▼
                     DYNAMIC RISK AGENT (ReAct)
             ┌────────────────────────────────────────┐
             │ • 4 Investigation Levels (0 to 3)      │
             │ • Multi-Factor CTI & Token Correlation │
             │ • Safe Reasoning Summary Attribution   │
             └──────────────────┬─────────────────────┘
                                │ Proposed Decision
                                ▼
                     POLICY GUARDRAIL ENGINE
             ┌────────────────────────────────────────┐
             │ • 5 Response Tiers (LOW to REMEDIATE)  │
             │ • Permitted Action Validation          │
             │ • Financial Movement Disallowance      │
             └──────────────────┬─────────────────────┘
                                │ Authorized Action
                                ▼
                     RESPONSE & VERIFICATION LAYER
             ┌────────────────────────────────────────┐
             │ • Non-Destructive Token Revocation     │
             │ • Simulated Step-Up 2FA Challenge      │
             │ • Post-Action State Query Verification │
             └──────────────────┬─────────────────────┘
                                │ Action Result
                                ▼
                     SHA-256 AUDIT LEDGER & DB
             ┌────────────────────────────────────────┐
             │ • Tamper-Evident SHA-256 Hash Chain    │
             │ • AES-256-GCM Authenticated Encryption │
             │ • Versioned KMS Key Provider           │
             └────────────────────────────────────────┘
```
