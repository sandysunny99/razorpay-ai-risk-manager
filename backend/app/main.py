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

# Create Database tables
Base.metadata.create_all(bind=engine)

# Seed initial data
with SessionLocal() as db:
    seed_initial_data(db)

app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic security layer for payment risk, card exposure, token protection, and controlled remediation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(risk_router, prefix=settings.API_V1_STR)
app.include_router(cards_router, prefix=settings.API_V1_STR)
app.include_router(tokens_router, prefix=settings.API_V1_STR)
app.include_router(cases_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "status": "ONLINE",
        "version": "1.0.0",
        "docs": "/docs",
        "dry_run": settings.DRY_RUN
    }
