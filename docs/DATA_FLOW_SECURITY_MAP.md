# End-to-End Data Flow Security Map

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  
**Status**: Comprehensive Lifecycle Security Map Complete  

---

## 1. Sensitive Field Lifecycle Security Matrix

| Sensitive Field | 1. Ingestion Source | 2. Transport Security | 3. In-Memory Processing | 4. Storage at Rest | 5. Frontend Display | 6. Logging & Telemetry | 7. Retention & Deletion |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Account Number (PAN)** | Client / Merchant API | TLS 1.3 + WAF | Converted immediately to HMAC-SHA256 fingerprint & Masked PAN | **NEVER STORED.** Only `masked_pan` and `card_fingerprint` persisted. | Masked (`**** **** **** 4921`) | Scrubbed by regex Luhn DLP (`[REDACTED_PAN]`) | Instant in-memory zeroing |
| **Card Verification Value (CVV)** | Payment Gateway | TLS 1.3 | **PROHIBITED.** Stripped on API boundary. | **NEVER STORED.** | **NEVER DISPLAYED.** | Scrubbed by DLP | Immediate drop |
| **Payment Token (`tok_***`)** | Razorpay Vault Adapter | TLS 1.3 | Referenced by token ID | Stored in `payment_tokens` table | Full token ID visible to authorized SOC analyst | Masked in public logs (`tok_***123`) | Soft-delete / Revoked status retained for audit |
| **Customer Email** | Checkout / Merchant DB | TLS 1.3 | Used for profile risk lookup | Stored in `customers` table | Dynamic masked (`j***e@domain.com`) | Masked in standard logs | Retained according to merchant policy |
| **Customer IP Address** | Client HTTP Headers | TLS 1.3 | Geo-distance calculation | Stored in `transactions` table | Masked (`122.166.***.***`) | Masked in standard logs | Configurable 90-day retention |
| **HMAC Secret Key** | Environment / KMS | Internal bus | Ephemeral in-memory | Stored in OS environment / KMS only | **NEVER DISPLAYED.** | Scrubbed by DLP | Versioned key rotation |
| **AES-256 Master Key** | Environment / KMS | Internal bus | Ephemeral in-memory | Stored in OS environment / KMS only | **NEVER DISPLAYED.** | Scrubbed by DLP | Versioned key rotation |
| **Cloudflare Ray ID** | `CF-Ray` Header | TLS 1.3 | Request correlation | Stored in `audit_events` metadata | Displayed in SOC timeline | Logged for security tracing | 365-day audit retention |

---

## 2. Cryptographic & DLP Gates Diagram

```
 CLIENT REQUEST
      │ (HTTPS / TLS 1.3)
      ▼
[ GATE 1: API PERIMETER DLP ] ──► Detects & Blocks raw PAN / CVV candidate payloads
      │
      ▼
[ GATE 2: HMAC & TOKENIZATION ] ──► Generates HMAC-SHA-256 fingerprint & Masked PAN
      │
      ▼
[ GATE 3: AGENT SANITIZATION ] ──► System prompts receive ONLY masked PANs & safe context
      │
      ▼
[ GATE 4: DB WRITE ENCRYPTION ] ──► AES-256-GCM field encryption + Fingerprint storage
      │
      ▼
[ GATE 5: DB READ MASKING ] ──► Backend applies role-based Dynamic Masking before response
      │
      ▼
[ GATE 6: LOGGING DLP SCRUBBER ] ──► All loggers pass through Luhn & secret regex scrubbers
      │
      ▼
 SOC DASHBOARD / CLIENT RESPONSE (Zero Raw Secrets Exchanged)
```
