# FreeLLMAPI Analysis

## Repository Overview
FreeLLMAPI is a TypeScript-based monorepo that provides an OpenAI-compatible aggregation layer. It targets routing, failover, quota-tracking, and health-checking across many LLM providers (Cloudflare, Grok, Hugging Face, Cohere, etc.). It includes a client UI, a CLI, and a complex backend server.

## Architecture
The repository uses a workspace model (`shared`, `server`, `client`, `cli`). 
The `server` is heavily focused on multi-tenant key management, dynamic model grouping, complex bandit-based routing strategies, and arbitrary custom OpenAI-compatible endpoints.

## Provider System
Providers are defined in `server/src/providers/`. The `BaseProvider` (`base.ts`) defines the abstraction. It normalizes inputs (Prompts/Messages) into provider-specific formats and normalizes outputs into the OpenAI format. 

## Routing System
Defined in `server/src/services/router.ts` and `scoring.ts`. It's a massive implementation (~114KB) using multi-armed bandit strategies, speed scoring, intelligence scoring, rate limit headroom, and custom weights. 
**Netvrio Impact:** Far too complex and non-deterministic for a security policy layer. We need a simple, deterministic router.

## Failover
Implemented within the router. Retries are triggered based on error classification (`server/src/lib/error-classify.ts`).
**Netvrio Impact:** Useful pattern, but must be bounded strictly to avoid retry storms in the critical webhook path.

## Health
Provider health is managed in `server/src/services/health.ts` and `cooldown-probe.ts`. Tracks degradation and cooldowns.

## Rate Limiting
Managed in `server/src/services/ratelimit.ts`. It enforces per-key concurrency, RPM/RPD, and TPU limits using local or Redis state. 
**Netvrio Impact:** Important pattern. Rate limiting should prevent fraud spikes from causing runaway LLM costs, but without blocking deterministic fallback.

## API Normalization
Uses OpenAI-compatible schemas internally, translating back-and-forth in provider modules.

## Key Management
Keys are stored in SQLite and optionally encrypted. Usage is tracked per key.
**Netvrio Impact:** We do not need multi-tenant *key* management (users bringing their own keys), but we need secure multi-tenant *execution* context.

## Security Review
- **Custom Endpoints:** FreeLLMAPI allows custom OpenAI-compatible endpoints (`server/src/services/custom-endpoint.ts`). This is a major SSRF risk if exposed to untrusted inputs.
- **Payload Handling:** Generic payload pass-through risks sending raw PANs/CVVs if not carefully masked.
- **Dependencies:** Deep NPM dependency tree; we prefer sticking to Netvrio's existing Python dependencies (httpx, pydantic).

## Useful Modules (For Netvrio LLM Gateway)
| Module / Pattern | FreeLLMAPI path | Purpose | Category | Netvrio use | Modification required | Security concern | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Provider Abstraction | `providers/base.ts` | Base provider class | **PATTERN ONLY** | `backend/llm/interfaces.py` | Complete rewrite in Python | None | HIGH |
| Deterministic Routing | `services/router.ts` | Router abstraction | **ADAPT** | `backend/llm/router.py` | Strip bandit logic; make deterministic priority | None | HIGH |
| Schema Normalization | `shared/types.ts` | Request/Response | **ADAPT** | `backend/llm/schemas.py` | Restrict to strictly defined fields only | SSRF/Data leak if loose | HIGH |
| Safe Fallback | `services/router.ts` | Failover execution | **ADAPT** | `backend/llm/router.py` | Ensure deterministic policy takes over on fail | Bypass risk | HIGH |
| Provider Health | `services/health.ts` | Health tracking | **ADAPT** | `backend/llm/health.py` | Align with AVAILABLE/UNAVAILABLE/CONTRACT states | None | MED |

## Rejected Modules
- **Client & CLI:** `client/`, `cli/` (CATEGORY D - Do not import).
- **Custom Endpoints:** `services/custom-endpoint.ts` (CATEGORY D - SSRF risk).
- **Bandit/Stochastic Routing:** `services/scoring.ts` (CATEGORY D - Undesired non-determinism).
- **Key Budgeting/User Quotas:** (CATEGORY D - Not a multi-tenant SaaS for LLM access).
- **SQLite Key Storage:** (CATEGORY D - Netvrio uses environment/secrets manager for core keys).

## Netvrio Integration Design
**Goal:** Implement `backend/llm/` with `interfaces.py`, `schemas.py`, `router.py`, `health.py`, `policy.py`, and `providers/cloudflare.py`, etc. 
**Architecture:**
```
RiskLLMRequest -> RiskLLMRouter -> RiskLLMProvider -> Normalization -> Evidence Check -> Policy Engine
```

## Implementation Plan
Proceeding to Stage 2: Create `docs/freellmapi-integration-plan.md` outlining the specific Python files to create, the data flow, and security boundaries.

## Implemented Changes
*(To be completed in Stage 3)*

## Dependencies Added
*(To be completed in Stage 3)*

## Tests Added
*(To be completed in Stage 3)*

## Regression Results
*(To be completed in Stage 4)*

## Security Results
*(To be completed in Stage 5)*

## Remaining Limitations
*(To be completed in Stage 5)*

## Production Verification Status
*(To be completed in Stage 5)*
