# Razorpay Risk Manager Agent: System Architecture

## 1. Architectural Principles

The **Razorpay Risk Manager Agent** is designed according to 6 core architectural principles:
1. **Rule & Determinism First, LLM Orchestration Second**: High-frequency transaction filtering runs on microsecond-latency deterministic engines. The AI Agent is invoked for high-risk investigation, correlation, and response orchestration.
2. **Strict Cryptographic Security Boundary**: Raw PANs, CVVs, and sensitive payment data never cross into logging layers, LLM context, or external threat databases.
3. **Pluggable Threat Intelligence Providers**: Intelligence sources are decoupled behind an abstract base class (`ThreatIntelProvider`), allowing synthetic, on-premise, and external CTI feeds to be hot-swapped without modifying core logic.
4. **Enforced Policy Guardrails**: The LLM suggests actions, but only the deterministic `PolicyEngine` authorizes execution.
5. **Verified State Transition**: Employs the `ACT → VERIFY → RECALCULATE` loop to query the payment gateway for confirmed state changes before reducing risk scores.
6. **Zero-Bloat Minimalist Design**: Avoids fragile multi-agent framework overhead in favor of a clean, robust, tool-calling agent with predictable execution.

---

## 2. Component Diagram

```
                              ┌─────────────────────────────────────────┐
                              │      Razorpay Risk SOC Dashboard        │
                              │   (React 18 + TypeScript + Tailwind)    │
                              └────────────────────┬────────────────────┘
                                                   │ REST / WebSockets
                                                   ▼
                              ┌─────────────────────────────────────────┐
                              │          FastAPI Risk Gateway           │
                              │        /api/v1/risk, /cards, etc.       │
                              └────────────────────┬────────────────────┘
                                                   │
                ┌──────────────────────────────────┴──────────────────────────────────┐
                ▼                                                                     ▼
┌──────────────────────────────┐                                       ┌──────────────────────────────┐
│    Deterministic Engines     │                                       │      Risk Manager Agent      │
│ • Transaction Risk Engine    │                                       │ • Agent Loop Orchestrator    │
│ • Card Lifecycle Engine      │◄──────────────────────────────────────┤ • Tool Calling Engine        │
│ • Token & Zombie Detector    │                                       │ • Structured Explainer       │
│ • Exposure Correlation Engine│                                       └──────────────┬───────────────┘
└───────────────┬──────────────┘                                                      │
                │                                                                     ▼
                │                                                      ┌──────────────────────────────┐
                │                                                      │    Policy Guardrail Engine   │
                │                                                      │ • AUTO_EXECUTE               │
                │                                                      │ • REVIEW_REQUIRED            │
                │                                                      │ • NEVER_EXECUTE              │
                │                                                      └──────────────┬───────────────┘
                │                                                                     │
                ▼                                                                     ▼
┌──────────────────────────────┐                                       ┌──────────────────────────────┐
│  Threat Intel Providers      │                                       │    Response & Verification   │
│ • SyntheticProvider (Offline)│                                       │ • Razorpay Test Adapter      │
│ • BreachDumpProvider         │                                       │ • Vault Verification API     │
│ • DarkWebStealerProvider     │                                       │ • Recalculate Risk (94 → 21) │
└───────────────┬──────────────┘                                       └──────────────┬───────────────┘
                │                                                                     │
                └──────────────────────────────┬──────────────────────────────────────┘
                                               ▼
                              ┌─────────────────────────────────────────┐
                              │     Storage & Audit Ledger Engine       │
                              │  • SQLite / PostgreSQL Database         │
                              │  • Security Case Queue                  │
                              │  • Cryptographic Immutable Audit Log    │
                              └─────────────────────────────────────────┘
```

---

## 3. Data Flow: The 10-Step Investigation Sequence

1. **`OBSERVE`**: Transaction or alert arrives via API/Webhook.
2. **`DETECT`**: `TransactionRiskEngine` checks amount deviations, velocity spikes, and foreign geo-IP indicators.
3. **`INVESTIGATE`**: `AgentToolRegistry` pulls customer risk tier and card status.
4. **`CORRELATE`**: `ExposureCorrelationEngine` computes HMAC-SHA256 card fingerprint and searches CTI breach feeds.
5. **`REASON`**: Mathematical `RiskScoringEngine` computes normalized score ($0-100$) and factor weights.
6. **`ASSESS RISK`**: Evaluates severity classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
7. **`CHECK POLICY`**: `PolicyEngine` determines execution rights (`AUTO_EXECUTE` for token revocation; `REVIEW_REQUIRED` for card suspension).
8. **`ACT`**: Invokes `RazorpayPaymentAdapter.revoke_payment_token()`.
9. **`VERIFY`**: Queries gateway vault status to verify state transitioned to `REVOKED`.
10. **`AUDIT`**: Recalculates risk ($94 \rightarrow 21$), logs immutable `AuditEvent`, and dispatches `SecurityCase`.

---

## 4. Technology Stack Selection Rationale

| Layer | Selected Stack | Rationale |
|---|---|---|
| **Backend** | Python 3.11+, FastAPI, Pydantic v2 | High asynchronous throughput, strict type safety, auto-generated OpenAPI documentation |
| **ORM & DB** | SQLAlchemy 2.0, SQLite (Zero-config) | Portable, embedded local database with seamless migration path to PostgreSQL in production |
| **Security Layer** | HMAC-SHA256, Luhn validation, Regex DLP | Zero raw PAN leakage, mathematical card validation, and PCI-DSS compliance |
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide | Instant HMR, SOC dark-mode aesthetic, real-time investigation timeline visualization |
