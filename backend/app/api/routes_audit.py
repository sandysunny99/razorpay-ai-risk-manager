from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import AuditEvent
from app.models.schemas import AuditEventResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("/events", response_model=List[AuditEventResponse])
def list_audit_events(db: Session = Depends(get_db)):
    events = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).all()
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
