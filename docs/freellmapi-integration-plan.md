# FreeLLMAPI Integration Plan for Netvrio (Revised)

## Reconnaissance Wording
Initial repository reconnaissance and targeted source analysis completed.

## Provider Health Model
Provider health tracks exact states:
AVAILABLE, UNAVAILABLE, MISCONFIGURED, TIMEOUT, ERROR, NOT_VERIFIED.

## Advisory vs Final Action
- LLM response produces `recommended_action`.
- Deterministic Policy Engine independently produces `final_action`.
- The LLM recommendation is NEVER the final system action.

## Safe Failure Contract
- **Provider unavailable:** deterministic risk path continues; no fabricated AI output; deterministic Policy Engine decides.
- **Provider timeout:** bounded retry/fallback; if exhausted, deterministic path continues.
- **Malformed LLM response:** reject advisory; deterministic path continues.
- **Invalid evidence IDs:** reject advisory; deterministic path continues.
- **Prompt-injection content:** treat as untrusted; do not modify system instructions or policy.

## Evidence Validation
Evidence validation is a hard gate.
Tests will explicitly verify that LLM references to unknown evidence cause the advisory to be REJECTED.

## Provider Order
1. Cloudflare
2. Grok
3. Hugging Face
Stubs must report `NOT_VERIFIED` or `MISCONFIGURED` without live credentials.

## Custom Endpoints
Arbitrary user-controlled OpenAI-compatible endpoints are strictly forbidden.

## Data Protection
The LLM must never receive raw PAN, CVV, PIN, webhook signing secret, API key, JWT, authentication token, or database credentials.

## Tenant Isolation
Provider routing and state remains tenant-aware. Shared caches must use tenant-scoped identifiers.

## Audit
AI execution metadata records only: provider, model, request_id, latency, status, fallback_used, schema_valid, evidence_valid, failure_reason.

## Test Cases
Provider tests: primary success, primary timeout, primary rate limit, primary malformed response, primary failure + secondary success, all providers unavailable.
Security tests: sensitive data blocked, prompt injection ignored, unknown evidence rejected, LLM ALLOW cannot override deterministic BLOCK, LLM BLOCK cannot override deterministic REVIEW.
Health tests: all states verified.

## Architecture Location
Webhook Security -> Deterministic Risk Engine -> Evidence -> RiskLLMRouter -> Deterministic Policy Engine -> Audit.
