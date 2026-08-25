# Real-Time Telemetry & External API Integration Matrix

**System**: Razorpay AI Risk Manager Agent  
**Environment**: Production-Ready / Test Mode Hybrid  
**Security Posture**: Zero-Knowledge / Bounded Enrichment (PCI-DSS & RBI Compliant)

---

## 1. Architectural Integration Principles

External third-party APIs and telemetry feeds **NEVER** possess direct decision-making authority over payment state or token revocation. All external signals are bounded, sanitized via DLP, normalized into standard `SecurityEvent` schemas, and passed as **evidence** to the authoritative Risk Engine.

```
       +-------------------------------------------------------------+
       |                  External Telemetry Sources                 |
       |  [Razorpay Test Mode]  [URLhaus IOC Feed]  [Binlist Provider]|
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                   Sanitization & DLP Gate                   |
       |  • Luhn-verified PAN masking (**** **** **** 1234)          |
       |  • HMAC-SHA256 Blind Indexing                               |
       |  • API Key / Token / Secret Strip                           |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |               Normalized Event Ingestion Layer              |
       |  • Thread-safe Idempotency Deduplication (EventDeduplicator)|
       |  • In-Memory Pub/Sub Dispatch (EventBus)                    |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |            Authoritative Decision & Risk Engines            |
       |  • Dual-Layer Policy Engine (T=40 / T=75)                   |
       |  • Dynamic Risk Agent with Bounded Tools                    |
       |  • Tamper-Evident SHA-256 Chained Audit Ledger              |
       +-------------------------------------------------------------+
```

---

## 2. Integration Matrix

| Source / Provider | Integration Type | Auth / Security Mechanism | Cache / Rate Limit | Fail-Safe / Offline Fallback |
| :--- | :--- | :--- | :--- | :--- |
| **Razorpay Test Mode API** | Webhook & REST Adapter (`backend/app/integrations/razorpay_adapter.py`) | Basic Auth (`RAZORPAY_KEY_ID:RAZORPAY_KEY_SECRET`), Raw Body HMAC-SHA256 signature verification | Rate limit 100 req/min | `MockRazorpayAdapter` providing deterministic scenario fixtures |
| **URLhaus Malware & IOC Feed** | Threat Intelligence Provider (`backend/app/enrichment/threat_provider.py`) | API Key header (`Auth-Key`), SSL certificate validation | 1-Hour in-memory cache, 2.0s network timeout | `MockThreatProvider` with synthetic offline indicators |
| **Binlist / Card Metadata** | Bank Identification Number Provider (`backend/app/enrichment/bin_provider.py`) | Public REST / No sensitive PAN transmission (First 6-8 digits only) | 24-Hour TTL cache, 1 req/sec interval throttle | `MockBinProvider` with comprehensive Indian & Global IIN table |
| **Cloudflare Security Telemetry** | Edge WAF & Bot Management Adapter (`backend/app/integrations/cloudflare_adapter.py`) | Ray ID correlation, IP blind hashing | Event stream buffer | Deterministic edge bot & WAF mock generator |
| **Enterprise DLP Gate** | Data Loss Prevention Engine (`backend/app/security/dlp.py`) | Regex + Luhn Checksum + Cryptographic Salted Fingerprinting | In-memory stream processor | Fail-closed (Unsanitized payloads rejected at gateway) |

---

## 3. Webhook Cryptographic Verification Standard

All incoming webhooks at `/api/v1/webhooks/razorpay` require authentic HMAC-SHA256 signatures:

```python
# Raw body HMAC-SHA256 signature verification
expected_signature = hmac.new(
    key=settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
    msg=raw_body_bytes,
    digestmod=hashlib.sha256
).hexdigest()

is_valid = hmac.compare_digest(expected_signature, request_signature)
```

- **Replay Protection**: Event deduplicator validates idempotency keys for 24 hours.
- **Data Protection**: DLP engine intercepts payload before DB persistence or agent processing.
