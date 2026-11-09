import os

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.dependencies import get_current_tenant
from backend.audit.audit_log import AuditRecordModel, SqlAuditRepository

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
            .filter_by(merchant_id=tenant_id)
            .order_by(AuditRecordModel.id.desc())
            .limit(limit)
            .all()
        )
        return {"items": [_safe_summary(r) for r in rows]}


@router.get("/summary")
def audit_summary(tenant_id: str = Depends(get_current_tenant)):
    """Aggregate decision counts for the calling tenant (drives the dashboard)."""
    with audit_repo.Session() as session:
        rows = session.query(AuditRecordModel).filter_by(merchant_id=tenant_id).all()
        counts = {d: 0 for d in DECISIONS}
        zombie = 0
        scores = []
        for r in rows:
            payload = r.record_payload or {}
            decision = payload.get("decision")
            if decision in counts:
                counts[decision] += 1
            if payload.get("zombie_detected"):
                zombie += 1
            if isinstance(payload.get("risk_score"), (int, float)):
                scores.append(float(payload["risk_score"]))
        return {
            "total": len(rows),
            "decisions": counts,
            "zombie_detected": zombie,
            "average_risk_score": round(sum(scores) / len(scores), 1) if scores else None,
            "chain_verified": audit_repo.verify_chain(),
        }


@router.get("/{audit_id}")
def get_audit(audit_id: str, tenant_id: str = Depends(get_current_tenant)):
    with audit_repo.Session() as session:
        # Enforce tenant ownership at query level
        record = session.query(AuditRecordModel).filter_by(audit_id=audit_id, merchant_id=tenant_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Audit not found or access denied")

        # Return only safe metadata
        safe_metadata = _safe_summary(record)
        safe_metadata["chain_verified"] = audit_repo.verify_chain()
        return safe_metadata
