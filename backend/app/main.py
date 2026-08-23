from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.db.seed_data import seed_initial_data

from app.api.routes_risk import router as risk_router
from app.api.routes_cards import router as cards_router
from app.api.routes_tokens import router as tokens_router
from app.api.routes_cases import router as cases_router
from app.api.routes_audit import router as audit_router
from app.api.routes_demo import router as demo_router
from app.api.routes_evaluation import router as evaluation_router
from app.api.routes_exposure import router as exposure_router
from app.api.routes_security import router as security_router
from app.api.routes_health import router as health_router

# Create Database tables
Base.metadata.create_all(bind=engine)

# Seed initial data
with SessionLocal() as db:
    seed_initial_data(db)

app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic security layer for payment risk, card exposure, token protection, and controlled remediation.",
    version="2.0.0-rc1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security Headers & Caching Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path.startswith("/api/v1/risk") or request.url.path.startswith("/api/v1/tokens"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router)
app.include_router(risk_router, prefix=settings.API_V1_STR)
app.include_router(cards_router, prefix=settings.API_V1_STR)
app.include_router(tokens_router, prefix=settings.API_V1_STR)
app.include_router(cases_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)
app.include_router(evaluation_router, prefix=settings.API_V1_STR)
app.include_router(exposure_router, prefix=settings.API_V1_STR)
app.include_router(security_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "status": "ONLINE",
        "version": "2.0.0-rc1",
        "docs": "/docs",
        "dry_run": settings.DRY_RUN
    }
