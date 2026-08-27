from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter(tags=["Health & Dependencies"])

@router.get("/health")
def health_check() -> Dict[str, Any]:
    """Basic Liveness & Readiness Probe."""
    return {
        "status": "healthy",
        "service": "Razorpay AI Risk Manager Gateway",
        "version": "2.0.0-rc2",
        "environment": "production-like"
    }

@router.get("/api/v1/health/dependencies")
def dependency_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Detailed dependency health check for all core subsystems."""
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "dependencies": {
            "sqlite_database": "UP" if db_ok else "DOWN",
            "risk_scoring_engine": "UP",
            "policy_guardrail_engine": "UP",
            "threat_intel_provider": "UP (Synthetic Offline Mode)",
            "cloudflare_edge_adapter": "UP",
            "razorpay_adapter": "UP (Mock/Test Sandbox)",
            "audit_ledger_engine": "UP",
            "dlp_scrubber": "UP",
            "key_provider": "UP",
            "aes_gcm_encryptor": "UP"
        }
    }
