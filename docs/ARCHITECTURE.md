# Architecture

## Pipeline Overview

```mermaid
flowchart TD
    E[Payment Event] --> W[Webhook/API Ingress]
    
    subgraph Security Layer
        W --> H[HMAC Verification]
        H --> R[Replay + Idempotency]
        R --> T[Tenant Validation]
        T --> D[DLP / Field Scrubber]
    end
    
    subgraph Analysis Layer
        D --> DR[Deterministic Risk Engine]
        D --> Z[Zombie Card Saver]
        DR --> EV[Evidence Package]
        Z --> EV
    end
    
    subgraph AI Boundary ["UNTRUSTED / ADVISORY ONLY"]
        EV -.-> AI[AI Advisory]
    end
    
    subgraph Decision Layer ["FINAL ACTION AUTHORITY"]
        EV --> SV[Schema + Evidence Validation]
        AI -.-> SV
        SV --> PE[Deterministic Policy Engine]
    end
    
    PE --> OUT[ALLOW / REVIEW / BLOCK / QUARANTINE]
    
    subgraph Observability
        OUT --> A[Audit Trail]
        OUT --> TEL[Telemetry]
    end
```

## Security Boundaries

### 1. Webhook Security
All incoming events undergo strict validation. HMAC ensures payload integrity, the idempotency layer rejects replays, and the tenant boundary verifies the `x-tenant-id` matches the payload's `merchant_id`.

### 2. AI Advisory Boundary
The AI output is treated strictly as **Untrusted / Advisory Only**. It is validated for evidence integrity (it cannot cite fake evidence IDs) and it cannot override the Deterministic Policy Engine. The LLM has zero direct remediation authority (e.g., it cannot execute a refund or revoke a token).

### 3. Deterministic Policy Authority
The **Deterministic Policy Engine** is the ultimate authority. It evaluates the deterministic risk assessment, the Zombie Card Saver signals, and the AI advisory (if available and valid). If the LLM is unavailable or compromised, the deterministic path ensures safe default handling.

### 4. Audit Trail
Every decision is securely logged with cryptographic hashing linking events to their audit records. Tenant isolation is enforced during audit retrieval.
