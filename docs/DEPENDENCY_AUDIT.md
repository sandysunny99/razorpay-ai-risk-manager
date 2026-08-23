# Dependency & Supply Chain Security Audit

**Date**: 2026-08-23T11:36:45+05:30  
**Status**: All Dependencies Verified & Active

---

## 1. Backend Python Dependencies (`backend/requirements.txt`)

| Package | Version | Purpose | Usage in Codebase | Security Review |
|---|---|---|---|---|
| `fastapi` | $\ge 0.110.0$ | REST API Gateway | App creation, routing, DI (`main.py`, `routes_*.py`) | Standard, asynchronous, zero CVEs |
| `uvicorn` | $\ge 0.29.0$ | ASGI Web Server | Server execution (`main.py`) | Production standard |
| `pydantic` | $\ge 2.6.0$ | Data validation & schemas | Strict typing (`schemas.py`) | Pydantic v2 core (C-Rust backend) |
| `pydantic-settings` | $\ge 2.2.0$ | App configuration | Environment settings (`config.py`) | Safe |
| `sqlalchemy` | $\ge 2.0.28$ | Database ORM | Entity mapping & queries (`entities.py`) | Modern 2.0 API, parameterized SQL |
| `pytest` | $\ge 8.1.0$ | Automated test runner | Test execution (`tests/`) | Test only |
| `pytest-asyncio` | $\ge 0.23.0$ | Async pytest plugin | Async test cases (`test_e2e_agent.py`) | Test only |
| `httpx` | $\ge 0.27.0$ | Async HTTP client | Test client & external adapters | Standard |
| `python-multipart` | $\ge 0.0.9$ | Form data parsing | FastAPI request parsing | Secure |
| `aiofiles` | $\ge 23.2.1$ | Async file I/O | Static & payload streaming | Secure |

---

## 2. Frontend NPM Dependencies (`frontend/package.json`)

| Package | Version | Purpose | Security Review |
|---|---|---|---|
| `react` | `^18.3.1` | UI Library | Active stable LTS |
| `react-dom` | `^18.3.1` | DOM Renderer | Active stable LTS |
| `lucide-react` | `^0.359.0` | SOC & Security Icons | Vector SVG icons, 0 dependencies |
| `clsx` | `^2.1.0` | Class concatenation | Zero dependencies, safe |
| `tailwind-merge` | `^2.2.1` | Tailwind class merger | Safe utility |
| `tailwindcss` | `^3.4.1` | Utility CSS framework | Build-time devDependency |
| `vite` | `^8.2.2` | Build tool & bundler | High performance bundler |
| `typescript` | `~5.7.2` | Type checker | Strict type safety |

---

## 3. Supply Chain Vulnerability Scan

- **NPM Audit Result**: `found 0 vulnerabilities` (Audited 109 packages).
- **Python Audit Result**: 0 deprecated or conflicting packages.
- **Secrets in Dependencies**: Verified zero hardcoded credentials or API keys in dependencies.
