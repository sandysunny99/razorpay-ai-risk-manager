# Repository Structure

```text
RAZORPAY AI Risk Manager (C:\Users\sunny\Downloads\RAZAORPAY AI)
├─ .dockerignore
├─ .env.example
├─ .git, .gitattributes, .gitignore
├─ .pytest_cache, .ruff_cache, .trivyignore
├─ .venv (project‑local virtual environment)
├─ backend
│   ├─ alembic, alembic.ini
│   ├─ app
│   │   ├─ api (15 route modules)
│   │   ├─ agent (risk_agent.py, tools.py)
│   │   ├─ core (config, database, telemetry)
│   │   ├─ engines (audit_ledger.py, policy_engine.py, risk_scorer.py, …)
│   │   └─ main.py (FastAPI entry point)
│   └─ requirements.txt, risk_manager.db
├─ dev
│   ├─ context-mode   (Node‑based developer tool)
│   ├─ code-review-graph (Python tool, not yet installed)
│   └─ token-savior   (Python tool, not yet installed)
├─ docs   (project documentation)
├─ evaluation   (test sets, frozen evaluation data)
├─ frontend   (React SPA, built into /dist at runtime)
├─ scripts   (utility scripts, CI helpers)
├─ sandbox   (empty now – will hold synthetic canary files)
├─ Dockerfile, docker‑compose.yml, render.yaml
└─ README.md, SECURITY.md, CHANGELOG.md, pyproject.toml, pytest.ini
```

Only the `backend/app` package contains production code. All other folders are development‑oriented tooling, documentation, or CI assets.
