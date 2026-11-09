# Gate 12: OpenTelemetry Security Boundaries

## Engineering Status
**IMPLEMENTED**

## Verification Status
**VERIFIED** (152 authoritative tests passed)

## Observability Controls Verified
- **Telemetry Verification**: An explicit test utilizing `InMemorySpanExporter` captured emitted spans and successfully asserted that PAN, CVV, and API Key string markers *did not* leak into the exported trace attributes or events. 
- **Central Sanitizer**: A centralized, recursive sanitizer strictly sweeps structured telemetry dicts for forbidden keys. 
- **Provider States**: Model integrations are correctly documented as **HTTP contract tested**, returning `STUB / UNAVAILABLE`. Live providers are NOT tested. Model failures emit latency, HTTP status, and error class, never exposing raw failure output or authentication tokens.
- **Correlation Propagation**: `x-correlation-id` dynamically propagates from middleware into risk engine, memory, providers, and audit trails using telemetry-safe strings.

## Limitations
- OpenTelemetry Exporter defaults to `ConsoleSpanExporter` for testing. Target environment configuration `OTEL_EXPORTER_MODE=otlp` is stubbed and **unverified**. Production OTLP deployment is not yet claimed. 
- The telemetry leakage test strictly verifies the `InMemorySpanExporter` path. External log/metrics sinks were not tested in this environment.
