from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import Role, get_current_user, verify_role
from app.core.database import get_db
from app.engines.token_risk import TokenRiskEngine
from app.integrations.razorpay_adapter import RazorpayPaymentAdapter
from app.models.entities import Card, PaymentToken
from app.models.schemas import TokenResponse, ZombieTokenAlert

router = APIRouter(prefix="/tokens", tags=["Tokens"])
token_engine = TokenRiskEngine()
razorpay = RazorpayPaymentAdapter()

@router.get("", response_model=List[TokenResponse])
def list_tokens(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(PaymentToken)
    if current_user.get("role") != Role.ADMIN.value:
        user_merchant = current_user.get("merchant_id", "default")
        query = query.filter(PaymentToken.merchant_id == user_merchant)
    tokens = query.all()
    resp = []
    for tok in tokens:
        card = db.query(Card).filter(Card.card_id == tok.card_id).first()
        tok_eval = token_engine.evaluate(tok, card) if card else {"is_zombie": False, "zombie_reason": None}
        resp.append(TokenResponse(
            token_id=tok.token_id,
            card_id=tok.card_id,
            customer_id=tok.customer_id,
            merchant_id=tok.merchant_id,
            status=tok.status,
            token_age_days=tok.token_age_days,
            usage_count=tok.usage_count,
            last_used_at=tok.last_used_at,
            is_zombie=tok_eval["is_zombie"],
            zombie_reason=tok_eval["zombie_reason"]
        ))
    return resp

@router.get("/zombies", response_model=List[ZombieTokenAlert])
def get_zombie_tokens(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = (
        db.query(PaymentToken, Card)
        .join(Card, PaymentToken.card_id == Card.card_id)
    )
    if current_user.get("role") != Role.ADMIN.value:
        user_merchant = current_user.get("merchant_id", "default")
        query = query.filter(PaymentToken.merchant_id == user_merchant)
    tokens_with_cards = query.all()
    return token_engine.detect_zombie_tokens(tokens_with_cards)

@router.post("/{token_id}/revoke")
async def revoke_token_endpoint(
    token_id: str,
    current_user: dict = Depends(verify_role(Role.ADMIN)),
    db: Session = Depends(get_db)
):
    tok = db.query(PaymentToken).filter(PaymentToken.token_id == token_id).first()
    if not tok:
        raise HTTPException(status_code=404, detail=f"Token '{token_id}' not found")

    user_merchant = current_user.get("merchant_id", "default")
    if current_user.get("role") != Role.ADMIN.value and tok.merchant_id != user_merchant:
        raise HTTPException(status_code=403, detail="Forbidden: Token belongs to another merchant")

    result = await razorpay.revoke_payment_token(token_id)
    tok.status = "REVOKED"
    db.commit()
    return result
