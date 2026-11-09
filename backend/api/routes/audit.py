import os
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func

from backend.api.dependencies import get_current_tenant
from backend.audit.audit_log import AuditRecordModel, SqlAuditRepository
from backend.realtime.bus import event_bus

router = APIRouter()

db_url = os.environ.get("AUDIT_DB_URL", "sqlite:///netvrio_audit.db")
audit_repo = SqlAuditRepository(db_url)

DECISIONS = ("ALLOW", "REVIEW", "BLOCK", "QUARANTINE")


def _safe_summary(record: AuditRecordModel) -> dict:
    """Metadata-only projection of an audit record. Never returns the raw payload."""
    payload = record.record_payload or {}
    return {
        "audit_id": record.audit_id,
        "event_id": record.event_id,
        "merchant_id": record.merchant_id,
        "correlation_id": record.correlation_id,
        "timestamp": record.timestamp,
        "decision": payload.get("decision"),
        "risk_score": payload.get("risk_score"),
        "risk_level": payload.get("risk_level"),
        "zombie_detected": bool(payload.get("zombie_detected", False)),
        "reason_codes": list(payload.get("reason_codes") or []),
        "record_hash": record.current_hash,
    }


@router.get("")
def list_audit_records(
    limit: int = Query(default=25, ge=1, le=100),
    tenant_id: str = Depends(get_current_tenant),
):
    """Most recent audit records for the calling tenant only."""
    with audit_repo.Session() as session:
        rows = (
            session.query(AuditRecordModel)
            .filter_by(merchant_id=tenant_id, record_type="decision")
            .order_by(AuditRecordModel.id.desc())
            .limit(limit)
            .all()
        )
        resolutions = _resolutions_for(session, tenant_id, [r.audit_id for r in rows])
        items = []
        for r in rows:
            item = _safe_summary(r)
            item["resolution"] = resolutions.get(r.audit_id)
            items.append(item)
        return {"items": items}


@router.get("/summary")
def audit_summary(tenant_id: str = Depends(get_current_tenant)):
    """Aggregate decision counts for the calling tenant, computed in SQL (no full-table load)."""
    payload = AuditRecordModel.record_payload
    decision_col = payload["decision"].as_string()
    with audit_repo.Session() as session:
        base = session.query(AuditRecordModel).filter(
            AuditRecordModel.merchant_id == tenant_id, AuditRecordModel.record_type == "decision"
        )
        counts = {d: 0 for d in DECISIONS}
        for decision, n in (
            base.with_entities(decision_col, func.count()).group_by(decision_col).all()
        ):
            if decision in counts:
                counts[decision] = n
        total = base.count()
        zombie = base.filter(payload["zombie_detected"].as_boolean().is_(True)).count()
        avg = base.with_entities(func.avg(payload["risk_score"].as_float())).scalar()
        return {
            "total": total,
            "decisions": counts,
            "zombie_detected": zombie,
            "average_risk_score": round(float(avg), 1) if avg is not None else None,
            "chain_verified": audit_repo.verify_chain_incremental(),
        }


@router.get("/verify")
def audit_verify_full(tenant_id: str = Depends(get_current_tenant)):
    """Full re-hash of the whole ledger (O(n)); catches out-of-band edits to old rows."""
    return {"chain_verified": audit_repo.verify_chain(), "scope": "full"}


@router.get("/{audit_id}")
def get_audit(audit_id: str, tenant_id: str = Depends(get_current_tenant)):
    with audit_repo.Session() as session:
        # Enforce tenant ownership at query level
        record = session.query(AuditRecordModel).filter_by(audit_id=audit_id, merchant_id=tenant_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Audit not found or access denied")

        # Return only safe metadata
        safe_metadata = _safe_summary(record)
        safe_metadata["resolution"] = _resolutions_for(session, tenant_id, [audit_id]).get(audit_id)
        safe_metadata["chain_verified"] = audit_repo.verify_chain_incremental()
        return safe_metadata


# ── Analyst resolution of REVIEW decisions ──────────────────────────────────────────────────

class ResolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["APPROVE", "DECLINE"]


def _resolution_id(audit_id: str) -> str:
    return f"res_{audit_id}"


def _resolutions_for(session, tenant_id: str, audit_ids: list) -> dict:
    if not audit_ids:
        return {}
    rows = (
        session.query(AuditRecordModel)
        .filter(
            AuditRecordModel.merchant_id == tenant_id,
            AuditRecordModel.record_type == "resolution",
            AuditRecordModel.audit_id.in_([_resolution_id(a) for a in audit_ids]),
        )
        .all()
    )
    return {
        r.record_payload.get("resolves"): {"action": r.record_payload.get("action"), "timestamp": r.timestamp}
        for r in rows
    }


@router.post("/{audit_id}/resolution")
def resolve_review(audit_id: str, body: ResolutionRequest, request: Request,
                   tenant_id: str = Depends(get_current_tenant)):
    """Record an analyst's outcome for a REVIEW decision as its own hash-chained audit record."""
    with audit_repo.Session() as session:
        record = session.query(AuditRecordModel).filter_by(
            audit_id=audit_id, merchant_id=tenant_id, record_type="decision"
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="Audit not found or access denied")
        if (record.record_payload or {}).get("decision") != "REVIEW":
            raise HTTPException(status_code=409, detail="Only REVIEW decisions can be resolved")
        if _resolutions_for(session, tenant_id, [audit_id]):
            raise HTTPException(status_code=409, detail="Decision already resolved")
        event_id = record.event_id

    correlation_id = getattr(request.state, "correlation_id", "unknown")
    resolution = {
        "audit_id": _resolution_id(audit_id),
        "event_id": event_id,
        "merchant_id": tenant_id,
        "correlation_id": correlation_id,
        "timestamp": int(time.time()),
        "record_type": "resolution",
        "resolves": audit_id,
        "action": body.action,
        "actor": "demo_analyst",  # Production auth is not connected; there is no real identity yet.
    }
    try:
        record_hash = audit_repo.append_record(resolution)
    except Exception:
        # Unique audit_id: a concurrent resolution won the race.
        raise HTTPException(status_code=409, detail="Decision already resolved") from None
    event_bus.publish(tenant_id, {
        "outcome": "RESOLVED", "source": "analyst", "event_id": event_id, "resolves": audit_id,
        "resolution": body.action, "correlation_id": correlation_id,
    })
    return {"audit_id": audit_id, "resolution": body.action, "record_hash": record_hash}
