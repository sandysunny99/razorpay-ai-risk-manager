from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base


class MerchantWebhookRegistration(Base):
    __tablename__ = "merchant_webhook_registrations"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(String(64), unique=True, index=True, nullable=False)  # opaque UUID4 or ULID
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False, index=True)
    razorpay_webhook_id = Column(String(64), nullable=True)  # optional Razorpay management API ID
    secret = Column(String(128), nullable=False)  # plaintext secret for HMAC verification
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationship can be added later if needed
