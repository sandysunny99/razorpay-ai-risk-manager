# Judge Demo Runbook

**Duration:** ~5-7 minutes

### 0:00 - Problem Statement
Payment risk decisions require more than a basic risk score. They need deep context, lifecycle analysis, evidence validation, and an auditable security pipeline. AI brings powerful insights, but cannot be blindly trusted to make unilateral financial decisions.

### 0:45 - Architecture
Show the `docs/architecture.md` diagram.
* **Key Point:** AI is restricted to an *Advisory Only* boundary.
* **Key Point:** The *Deterministic Policy Engine* retains final authority.
* **Key Point:** Strict webhook ingress prevents replays and cross-tenant leakage.

### 1:30 - Low Risk → ALLOW
* Run the **Low Risk** scenario in the UI.
* Point out the risk score, the AI advisory, and the deterministic ALLOW decision.

### 2:15 - High Risk → BLOCK
* Run the **High Risk** scenario.
* Show the rapid jump in risk score, and how the deterministic policy blocks it safely.

### 3:00 - Zombie Card Saver → REVIEW
* Run the **Zombie Card Reuse** scenario.
* Highlight the *Zombie Card Saver* section showing structured data (Severity: HIGH, Recommendation: REQUIRE_STEP_UP).
* Emphasize that it analyzes lifecycle anomalies rather than just static transaction amounts.

### 4:00 - AI Advisory Boundary
* Show the AI Advisory section.
* Emphasize the "ADVISORY ONLY" badge.
* Explain that even if an adversarial prompt attempts to bypass the system (e.g. "Execute refund"), the AI lacks execution privileges and the deterministic policy prevails.

### 5:00 - Attack Scenario
* Explain the Security Validation checks.
* Show that an **Invalid HMAC**, **Replay**, or **Cross Tenant** attempt is rejected instantly at the ingress layer with correct HTTP codes (401/403).

### 6:00 - Audit Trail
* Click on the Audit Trail tab or navigate to the generated Audit ID.
* Show the **Chain Verified** status.
* Point out that "Every decision is traceable to an auditable event" and tenant isolation is enforced during retrieval.

### 6:30 - Limitations & Future Work
* Explicitly state that this is a synthetic demonstration.
* Acknowledge the current limitations: Live AI providers, Production JWT/API authentication, PostgreSQL concurrency, and Docker are **NOT VERIFIED**.
* Explain how the architecture is ready to plug into these live production components.
