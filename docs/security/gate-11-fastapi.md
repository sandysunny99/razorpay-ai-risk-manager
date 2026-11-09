# Gate 11: FastAPI Production-Style Integration

## Engineering Status
**IMPLEMENTED**

## Verification Status
**VERIFIED** (152 authoritative tests passed)

## Security Constraints Verified
- **Webhook Secret Fallback Removed**: Non-test mode now requires an explicit `WEBHOOK_SECRET` environment variable or it will fail closed (500 Server Configuration Error).
- **Tenant Identification vs Authentication**: The API currently utilizes **Tenant Identification** for the prototype (trusting `x-tenant-id` header in TEST mode). A placeholder `ProductionTenantAuthProvider` has been stubbed which will fail closed (501 Not Implemented) if deployed to production without a real JWT/API Key implementation. 
- **Tenant Authorization**: Repositories natively filter by `merchant_id=tenant_id`, proven via `HTTP 404` enumeration test on cross-tenant requests. The tenant ID used for authorization is strictly bound to the authenticated principal.
- **Payload Limits**: Max 1MB payload enforced before parsing.
- **Strict Pydantic Validation**: The dynamic prototype payload has been replaced with a strict `WebhookPayload` Pydantic schema. It enforces types, restricts unknown fields natively where practical, and bounds lengths. 
- **HMAC over bytes**: HMAC validation operates on raw request bytes, strictly prior to Pydantic parsing.
- **Replay / Timestamp**: Strict expiry check immediately after unpacking event_id.
- **Idempotency Locks**: Redis `set_nx_ex` is evaluated *only* after HMAC and timestamp verification.
- **Zombie Exception Removed**: Raw PAN overrides are strictly abolished. Raw PAN entry without a vault token throws `ValueError(400)` natively.
- **Security Headers & CORS**: The application enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Content-Security-Policy: default-src 'self'`. CORS explicitly rejects unconfigured origins.
- **Sanitized Errors**: Core execution exceptions map to HTTP 500 without stack-traces, file paths, SQL, or secrets.

## Cases & Audit APIs
- **GET /cases/{case_id}**: Validates tenant ownership.
- **GET /audit/{audit_id}**: Strictly filters payloads, providing only secure metadata (`decision`, `timestamp`) and a `chain_verified` marker.

*Note: SQL scaling remains verified for SQLite single-process prototyping. Real multi-process scalability requires PostgreSQL.*
