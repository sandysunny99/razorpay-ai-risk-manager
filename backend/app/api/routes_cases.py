from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import SecurityCase
from app.models.schemas import SecurityCaseResponse

router = APIRouter(prefix="/cases", tags=["Security Cases"])

@router.get("", response_model=List[SecurityCaseResponse])
def list_cases(db: Session = Depends(get_db)):
    cases = db.query(SecurityCase).order_by(SecurityCase.created_at.desc()).all()
    return [
        SecurityCaseResponse(
            case_id=c.case_id,
            severity=c.severity,
            card_id=c.card_id,
            token_id=c.token_id,
            customer_id=c.customer_id,
            merchant_id=c.merchant_id,
            risk_score=c.risk_score,
            reason=c.reason,
            status=c.status,
            assigned_to=c.assigned_to,
            actions_taken=c.actions_taken or [],
            timeline=c.timeline or [],
            created_at=c.created_at
        ) for c in cases
    ]

@router.get("/{case_id}", response_model=SecurityCaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    c = db.query(SecurityCase).filter(SecurityCase.case_id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    return SecurityCaseResponse(
        case_id=c.case_id,
        severity=c.severity,
        card_id=c.card_id,
        token_id=c.token_id,
        customer_id=c.customer_id,
        merchant_id=c.merchant_id,
        risk_score=c.risk_score,
        reason=c.reason,
        status=c.status,
        assigned_to=c.assigned_to,
        actions_taken=c.actions_taken or [],
        timeline=c.timeline or [],
        created_at=c.created_at
    )
