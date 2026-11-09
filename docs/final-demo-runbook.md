# Final Demo Runbook

**Duration:** ~5-7 minutes

## Opening
Netvrio is an AI Payment Risk & Security Platform focused on secure, merchant-aware payment-risk decisions.

## Architecture
**Payment Event**
-> Webhook/API Ingress
-> HMAC
-> Replay + Idempotency
-> Tenant Validation
-> DLP
-> Deterministic Risk Engine
-> Zombie Card Saver
-> Evidence
-> AI Advisory
-> Schema + Evidence Validation
-> Deterministic Policy Engine
-> ALLOW / REVIEW / BLOCK / QUARANTINE
-> Audit + Telemetry

## Demo
A. **Low Risk** -> ALLOW
B. **Medium Risk** -> REVIEW
C. **High Risk** -> BLOCK
D. **Zombie Card Saver** -> REVIEW
   - Severity: HIGH
   - Recommendation: REQUIRE_STEP_UP

## Security
E. **Replay** -> 401
F. **Invalid HMAC** -> 401
G. **Cross Tenant** -> 403
H. **Sensitive Field** -> 422

## AI Boundary
Explain that AI output is advisory and untrusted.
It cannot directly perform remediation.
The deterministic policy engine remains the final action authority.

## Audit
Show the audit event and chain verification.
