from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import Role, enforce_tenant_access, get_current_user
from app.core.database import get_db
from app.models.entities import SecurityCase
from app.models.schemas import SecurityCaseResponse

router = APIRouter(prefix="/cases", tags=["Security Cases"])

@router.get("", response_model=List[SecurityCaseResponse])
def list_cases(
    merchant_id: Optional[str] = Query(None, description="Filter cases by merchant ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_merchant = enforce_tenant_access(merchant_id, current_user)
    query = db.query(SecurityCase)
    if current_user.get("role") != Role.ADMIN.value:
        query = query.filter(SecurityCase.merchant_id == target_merchant)
    cases = query.order_by(SecurityCase.created_at.desc()).all()
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
def get_case(
    case_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(SecurityCase).filter(SecurityCase.case_id == case_id)
    if current_user.get("role") != Role.ADMIN.value:
        user_merchant = current_user.get("merchant_id", "default")
        query = query.filter(SecurityCase.merchant_id == user_merchant)
    c = query.first()
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
