"""Threat intelligence status, recent matches and (demo/admin) feed refresh."""
import asyncio
import hashlib
import hmac
import os
import re
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from backend.api.routes.live import get_stream_tenant, require_demo_mode
from backend.realtime.bus import event_bus
from backend.threat_intel.exposure import FINGERPRINT_RE, exposure_store
from backend.threat_intel.service import threat_intel

router = APIRouter()


@router.get("/status")
def intel_status(tenant_id: str = Depends(get_stream_tenant)):
    return threat_intel.status(tenant_id)


@router.get("/matches")
def intel_matches(limit: int = Query(default=50, ge=1, le=200), tenant_id: str = Depends(get_stream_tenant)):
    return {"items": threat_intel.store.recent_matches(tenant_id, limit)}


@router.post("/refresh")
async def intel_refresh(tenant_id: str = Depends(get_stream_tenant), _: None = Depends(require_demo_mode)):
    results = await asyncio.to_thread(threat_intel.refresh)
    return {"results": results, **threat_intel.status(tenant_id)}


# ── Card exposure ingestion (from an isolated collector such as the OnionClaw adapter) ─────

EXPOSURE_MAX_SKEW_S = 300
_DIGIT_RUN = re.compile(r"\d{12,}")


class ExposureFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fingerprint: str = Field(..., max_length=19)
    observed_at: Optional[int] = None
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    reference: str = Field(default="", max_length=120)

    @field_validator("fingerprint")
    @classmethod
    def _fp(cls, v: str) -> str:
        if not FINGERPRINT_RE.match(v):
            raise ValueError("fingerprint must be fp_ + 16 hex chars")
        return v

    @field_validator("reference")
    @classmethod
    def _no_numbers(cls, v: str) -> str:
        # A reference is a site label, never card data: refuse anything with long digit runs.
        if _DIGIT_RUN.search(v):
            raise ValueError("reference must not contain long digit sequences")
        return v


class ExposureReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str = Field(..., min_length=1, max_length=64)
    findings: List[ExposureFinding] = Field(..., max_length=1000)


@router.post("/exposures")
async def ingest_exposures(request: Request):
    secret = os.getenv("EXPOSURE_FEED_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="Exposure feed secret not configured")
    raw = await request.body()
    ts = request.headers.get("x-netvrio-timestamp", "")
    sig = request.headers.get("x-netvrio-signature", "")
    expected = "sha256=" + hmac.new(secret.encode(), ts.encode() + b"." + raw, hashlib.sha256).hexdigest()
    if not ts.isdigit() or not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")
    if abs(time.time() - int(ts)) > EXPOSURE_MAX_SKEW_S:
        raise HTTPException(status_code=401, detail="Replay or stale timestamp detected")
    try:
        report = ExposureReport.model_validate_json(raw)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Schema validation failed") from None

    new, to_revoke = exposure_store.report([f.model_dump() for f in report.findings], report.source)
    revoked = 0
    for tenant, tokens in to_revoke.items():
        for token in tokens:
            threat_intel.store.revoke_token(tenant, token)
        revoked += len(tokens)
        event_bus.publish(tenant, {"outcome": "EXPOSURE", "source": report.source, "tokens_revoked": len(tokens),
                                   "findings": len(report.findings)})
    return {"accepted": len(report.findings), "new": new, "tokens_revoked": revoked}


@router.get("/exposures")
def exposure_summary(tenant_id: str = Depends(get_stream_tenant)):
    return {**exposure_store.summary(), "configured": bool(os.getenv("EXPOSURE_FEED_SECRET"))}
