# Hackathon Evidence Index

| Artifact | Actual Path | Evidence SHA | Artifact Commit SHA | Purpose | Status |
|----------|-------------|--------------|---------------------|---------|--------|
| **R-002 implementation** | `backend/app/main.py`<br>`backend/app/api/routes_admin_webhook.py`<br>`backend/app/models/merchant_webhook_registration.py`<br>`backend/tests/test_admin_webhook_registration.py`<br>`backend/tests/test_controlled_webhook_endpoint.py` | `52b920bf50064799458c75856fb84c80c77e89de` | N/A | Verified risk-engine + merchant-webhook attribution that satisfies the R-002 security boundary. | VERIFIED_COMPLETE |
| **Security-regression evidence** | `docs/SECURITY_REGRESSION.md` | `52b920bf50064799458c75856fb84c80c77e89de` | UNKNOWN | Shows that the full security-regression suite passes after the R-002 implementation. | VERIFIED |
| **Zombie-Card-Saver evidence** | `backend/tests/test_zombie_card_saver.py` | `52b920bf50064799458c75856fb84c80c77e89de` | `55d2596490677339be60a46ae5b88ff2d7f335b4` | Detects reuse of card numbers; part of the security-regression package. | VERIFIED |
| **Evaluation evidence** | `evaluation/` | `52b920bf50064799458c75856fb84c80c77e89de` | `52b920bf50064799458c75856fb84c80c77e89de` | Controlled synthetic evaluation of risk scoring, policy enforcement, and merchant-aware security. | VERIFIED |
| **CI evidence** | `.github/workflows/ci.yml` (run #33246570471) | N/A | N/A | CI passed for the final push. | PASS |
| **CodeQL analysis** | `CODEQL` | N/A | N/A | CodeQL analysis status. | FORMALLY_BLOCKED |
| **Cybersecurity-Skills** | `docs/security-skills/` | N/A | `870b670081c49af8eb2a487745ad85f0058db4bb` | Developer-only reference material, byte-identical to upstream. | VERIFIED |
| **Documentation baseline** | `docs/` | N/A | `55d2596490677339be60a46ae5b88ff2d7f335b4` | Product-first documentation and hackathon documentation. | VERIFIED |
| **AgentMemory** | N/A | N/A | N/A | Developer-only runtime tool. | OPTIONAL / NOT_VERIFIED |
