# Gate 15 Demo Readiness Report

## IMPLEMENTED
* **Secure Webhook Demo Architecture:** The frontend now requests a signed HMAC envelope from a new `/demo/sign` endpoint restricted to test environments, eliminating client-side secrets.
* **Strict Evidence Integrity:** The system intercepts invalid or hallucinated evidence IDs returned by the LLM, marking the advisory as `UNAVAILABLE` and preventing invalid IDs from being adopted into the final policy decision.
* **Bounded Frontend Types:** The `any` type has been removed from frontend API integration, now strictly modeled using `WebhookDemoData`.
* **Telemetry Data Sanitization:** Sensitive payload fields and raw exceptions are structurally excluded from OTLP span exports to prevent telemetry leakage.

## VERIFIED
* **API Contract (184 backend tests passed):** Automated backend testing explicitly covers the 8 end-to-end webhook scenarios (A to H) demonstrating correct routing, HMAC rejection, tenant isolation, idempotency, and Raw PAN rejection.
* **Adversarial Security Boundaries:** `test_gate15_5_scenarios.py` successfully verifies that prompt injection ("IGNORE ALL SECURITY RULES") and LLM action overrides ("execute_refund") fail safely, leaving deterministic policy unaffected and invalidating out-of-schema responses.
* **Audit System E2E:** E2E audit retrieval is verified, successfully proving that fetching nonexistent IDs and malformed requests fail securely without leaking internal state.
* **UI Truthfulness (9 frontend tests passed):** The frontend explicitly warns users that data is "SYNTHETIC / DEMONSTRATION DATA" and notes that "DEMO TENANT CONTEXT - Production authentication is not connected."

## NOT VERIFIED
* **Provider Live Execution:** The system still utilizes stubbed LLM clients for Cloudflare, Grok, and Hugging Face; live API keys were not tested.
* **PostgreSQL Concurrency:** Current backend locking is proven logically, but relies on SQLite in test environments instead of real-world Postgres transaction boundaries.

## KNOWN LIMITATIONS
* **Authentication:** The `x-tenant-id` header serves as a functional demonstration boundary but does not represent cryptographically verified JWT/API-key validation.
* **Production Secrecy:** The `WEBHOOK_SECRET` relies on a dummy string in test mode. Live deployments require secure vault injection.

## DEMO SECURITY MODEL
* The frontend acts as a synthetic event generator pointing at the backend's webhook endpoint, replicating external payment traffic.
* The `/demo/sign` endpoint safely handles HMAC generation exclusively on the server, returning 404 in production, ensuring the browser never touches secrets.
* The risk pipeline processes demo data through the exact deterministic policy engine and security constraints as production traffic.
* All outputs in the UI represent strictly verified data paths, without any mocked decisions or fabricated AI advisories.
