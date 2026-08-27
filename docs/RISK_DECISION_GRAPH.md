# Risk Decision Call Graph

```mermaid
flowchart TD
    A[API Endpoint] -->|Call| B[risk_agent.py]
    B -->|Invoke| C[RiskScoringEngine]
    C -->|Compute| D[policy_engine.py::classify_risk_tier]
    D -->|Decision| E[Decision Outcome]
    E -->|Return| F[API Response]
    click B "file:///C:/Users/sunny/Downloads/RAZAORPAY%20AI/backend/app/agent/risk_agent.py#L350-L380" "risk_agent.py"
    click C "file:///C:/Users/sunny/Downloads/RAZAORPAY%20AI/backend/app/engines/risk_scorer.py#L120-L150" "risk_scorer.py"
    click D "file:///C:/Users/sunny/Downloads/RAZAORPAY%20AI/backend/app/engines/policy_engine.py#L45-L100" "policy_engine.py"
```

**Explanation**:
- The API router (e.g., `backend/app/api/routes_risk.py` line 39) calls `risk_agent.process_transaction`.
- `risk_agent` (lines 350‑380) delegates to `RiskScoringEngine` which calculates the numeric risk score.
- The score is passed to `PolicyEngine.classify_risk_tier` (lines 45‑100) to determine the action (`AUTO_EXECUTE`, `REVIEW_REQUIRED`, `NEVER_EXECUTE`).
- The final decision is returned to the API response.
