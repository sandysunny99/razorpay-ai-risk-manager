# Data Classification Policy & Sensitivity Taxonomy

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  
**Status**: Comprehensive Data Classification Approved  

---

## 1. Five-Tier Data Sensitivity Taxonomy

```
[ PUBLIC ] ──► [ INTERNAL ] ──► [ CONFIDENTIAL ] ──► [ RESTRICTED ] ──► [ HIGHLY RESTRICTED ]
(Open Docs)    (Merchant IDs)    (Customer PII)       (Masked PAN/Tokens) (Master Keys/Secrets)
```

| Sensitivity Tier | Data Elements | Storage Policy | Transmission Policy | Access Control & Masking Rule |
| :--- | :--- | :--- | :--- | :--- |
| **PUBLIC** | Documentation, OpenAPI schema, public health status, baseline benchmarks. | Plaintext in git / web. | Unrestricted over HTTPS. | Public read access; zero authentication required. |
| **INTERNAL** | Aggregated risk metrics, merchant names, rule IDs, investigation levels. | SQLite / PostgreSQL database. | TLS 1.2+ over HTTPS. | Role-Based Access Control (RBAC); scoped to authenticated merchant. |
| **CONFIDENTIAL** | Customer names, emails, phone numbers, transaction amounts, IP addresses, device IDs. | Database with field encryption (AES-256-GCM) where needed. | TLS 1.3 encrypted transit. | Dynamic masking applied on backend (`user***@email.com`, `122.166.***.***`). |
| **RESTRICTED** | Masked PANs (`**** **** **** 4921`), BINs (First 6), Payment Tokens (`tok_***`), CTI breach sources, SOC case notes. | Database with HMAC-SHA256 fingerprint indexing. | TLS 1.3 encrypted transit. | Masked format only; raw PAN never reconstructed. |
| **HIGHLY RESTRICTED** | Raw PANs (13-19 digits), CVVs, PINs, OTPs, Razorpay secrets, Cloudflare tokens, HMAC salt keys, AES-256 keys. | **NEVER STORED IN DATABASE OR LOGS.** Keys managed via KMS / environment. | In-memory only with ephemeral lifecycle. | **PROHIBITED FROM ENTERING LLM, FRONTEND, AUDIT LOGS, OR PERSISTENT STORAGE.** |

---

## 2. Cardholder & Sensitive Data Handling Rules

1. **Raw PAN Ingestion**: Any 13-19 digit card number matching the Luhn algorithm candidate is immediately tokenized or masked upon arrival at the API perimeter.
2. **Prohibited Authentication Secrets**: CVV, CVC, PIN, and OTP authentication secrets are rejected and never persisted.
3. **Cryptographic One-Way Fingerprinting**: Exposure matching uses `HMAC-SHA256(PAN, server_salt)` so that neither threat intelligence matching nor internal queries ever require raw card numbers.
4. **Agent & LLM Sanitization Boundary**: System prompts, agent reasoning traces, and tool arguments receive strictly masked PANs (`**** 4921`) and token identifiers.
