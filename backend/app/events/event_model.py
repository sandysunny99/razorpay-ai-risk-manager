from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    # Payment events
    PAYMENT_CREATED = "PAYMENT_CREATED"
    PAYMENT_AUTHORIZED = "PAYMENT_AUTHORIZED"
    PAYMENT_CAPTURED = "PAYMENT_CAPTURED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_REFUNDED = "PAYMENT_REFUNDED"

    # Card lifecycle events
    CARD_EXPIRED = "CARD_EXPIRED"
    CARD_REPLACED = "CARD_REPLACED"
    CARD_BLOCKED = "CARD_BLOCKED"
    CARD_SUSPENDED = "CARD_SUSPENDED"

    # Token lifecycle events
    TOKEN_CREATED = "TOKEN_CREATED"
    TOKEN_USED = "TOKEN_USED"
    TOKEN_FAILED = "TOKEN_FAILED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # Threat & Security events
    CARD_EXPOSURE_DETECTED = "CARD_EXPOSURE_DETECTED"
    THREAT_INTEL_MATCH = "THREAT_INTEL_MATCH"
    CLOUDFLARE_SECURITY_EVENT = "CLOUDFLARE_SECURITY_EVENT"
    RISK_SCORE_UPDATED = "RISK_SCORE_UPDATED"

    # Zombie Card Saver events
    ZOMBIE_CARD_DETECTED = "ZOMBIE_CARD_DETECTED"
    ZOMBIE_TOKEN_DETECTED = "ZOMBIE_TOKEN_DETECTED"
    ZOMBIE_ACTION_EXECUTED = "ZOMBIE_ACTION_EXECUTED"

    # Policy & Governance events
    POLICY_DECISION = "POLICY_DECISION"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    ACTION_VERIFIED = "ACTION_VERIFIED"
    DLP_EVENT = "DLP_EVENT"
    AUDIT_EVENT = "AUDIT_EVENT"

class SecurityEvent(BaseModel):
    """
    Standardized internal security and transaction event structure.
    """
    event_id: str
    event_type: EventType
    source: str = Field(default="INTERNAL", description="Source system: RAZORPAY_TEST, CLOUDFLARE, CTI, INTERNAL")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    card_fingerprint: Optional[str] = None
    token_id: Optional[str] = None
    transaction_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    risk_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
