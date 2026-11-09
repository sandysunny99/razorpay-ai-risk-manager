from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.api.routes import audit, cases, health, intel, live, razorpay, risk, webhooks, youpi
from backend.observability.middleware import SecurityObservabilityMiddleware
from backend.realtime.generator import all_generators, get_generator
from backend.runtime_env import demo_mode_enabled, is_production
from backend.threat_intel.service import threat_intel


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Optional: start live synthetic traffic for the demo tenant as soon as the API boots.
    if demo_mode_enabled() and os.getenv("NETVRIO_LIVE_AUTOSTART", "false").lower() == "true":
        get_generator(os.getenv("NETVRIO_LIVE_TENANT", "tenant_123")).start()
    threat_intel.start_background_refresh()  # no-op unless NETVRIO_TI_LIVE_FEEDS=true
    yield
    await threat_intel.stop()
    for gen in all_generators():
        await gen.stop()

app = FastAPI(title="Netvrio API", lifespan=lifespan)

# Swagger/ReDoc pull their assets from a CDN, so they get a relaxed CSP.
_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")
_STRICT_CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not request.url.path.startswith(_DOCS_PATHS):
            response.headers["Content-Security-Policy"] = _STRICT_CSP
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SecurityObservabilityMiddleware)

_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]


def _resolve_allowed_origins() -> list[str]:
    configured = os.environ.get("CORS_ALLOWED_ORIGINS", "")
    if configured:
        return [o.strip() for o in configured.split(",") if o.strip()]
    if is_production():
        return []  # Production must opt in explicitly.
    return list(_DEV_ORIGINS)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_allowed_origins(),
    # No cookies/credentials are used by the dashboard; tenant context travels in a header.
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["content-type", "x-signature", "x-tenant-id", "x-correlation-id"],
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(risk.router, prefix="/risk", tags=["Risk"])
app.include_router(cases.router, prefix="/cases", tags=["Cases"])
app.include_router(audit.router, prefix="/audit", tags=["Audit"])
app.include_router(live.router, prefix="/live", tags=["Live"])
app.include_router(intel.router, prefix="/intel", tags=["Threat Intel"])
app.include_router(razorpay.router, prefix="/integrations/razorpay", tags=["Razorpay"])
app.include_router(youpi.router, prefix="/integrations/youpi", tags=["YouPI-PG"])


# ── Optional: serve the built dashboard (single-container deploys) ──────────
# Frontend routes deliberately avoid the API prefixes (/health, /audit, ...).
_DIST = Path(os.environ.get("NETVRIO_FRONTEND_DIST", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
_SPA_ROUTES = ("/", "/threats", "/ledger", "/integrations")

if (_DIST / "index.html").is_file():
    if (_DIST / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    def _spa_index() -> FileResponse:
        return FileResponse(_DIST / "index.html")

    for _route in _SPA_ROUTES:
        app.add_api_route(_route, _spa_index, methods=["GET", "HEAD"], include_in_schema=False)

    if (_DIST / "favicon.svg").is_file():
        app.add_api_route(
            "/favicon.svg", lambda: FileResponse(_DIST / "favicon.svg"), methods=["GET"], include_in_schema=False
        )
