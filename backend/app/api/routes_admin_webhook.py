import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Merchant, MerchantWebhookRegistration
from app.security.auth import Role, verify_role

router = APIRouter(prefix="/admin", tags=["Admin Webhook Registration"])

@router.post("/merchants/{merchant_id}/webhook-registrations")
async def create_webhook_registration(
    merchant_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_role(Role.ADMIN)),
):
    """Provision a new webhook registration for a merchant.

    Returns the registration details **without** the secret.
    """
    # Verify merchant exists
    merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

    # Generate opaque endpoint_id and secret
    endpoint_id = uuid.uuid4().hex
    secret = secrets.token_hex(32)  # 64 hex chars

    registration = MerchantWebhookRegistration(
        endpoint_id=endpoint_id,
        merchant_id=merchant.id,
        secret=secret,
        active=True,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    # Return data without secret
    return {
        "registration_id": registration.id,
        "endpoint_id": registration.endpoint_id,
        "merchant_id": merchant.merchant_id,
        "razorpay_webhook_id": registration.razorpay_webhook_id,
        "active": registration.active,
        "created_at": registration.created_at,
    }
