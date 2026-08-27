from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.engines.audit_ledger import AuditLedgerEngine
from app.models.entities import AuditEvent
from app.models.schemas import AuditEventResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("/events", response_model=List[AuditEventResponse])
def list_audit_events(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=500, description="Max events to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """Return audit events with pagination support (limit/offset)."""
    events = (
        db.query(AuditEvent)
        .order_by(AuditEvent.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        AuditEventResponse(
            event_id=e.event_id,
            actor=e.actor,
            agent_decision=e.agent_decision,
            risk_score=e.risk_score,
            policy_evaluated=e.policy_evaluated,
            tool_used=e.tool_used,
            action_requested=e.action_requested,
            action_executed=e.action_executed,
            verification_result=e.verification_result,
            details=e.details or {},
            created_at=e.created_at
        ) for e in events
    ]

@router.get("/verify")
def verify_audit_chain(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Cryptographically validates the hash chain from genesis to head."""
    return AuditLedgerEngine.verify_chain_integrity(db)
