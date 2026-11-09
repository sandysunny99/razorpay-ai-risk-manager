from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class WebhookPayload(BaseModel):
    event_id: str = Field(..., max_length=100)
    timestamp: int
    merchant_id: str = Field(..., max_length=100)
    event_type: str = Field(default="payment_attempt", max_length=50)
    data: Dict[str, Any] = Field(default_factory=dict)

    # Allowed secure references
    token: Optional[str] = Field(default=None, max_length=255)
    fingerprint: Optional[str] = Field(default=None, max_length=255)

    # We allow card_pan to exist solely so we can explicitly reject it in the route
    card_pan: Optional[str] = Field(default=None, max_length=19)
    pan: Optional[str] = Field(default=None, max_length=19)

    model_config = ConfigDict(extra='forbid') # Strict webhook validation: forbid extra fields for security (Phase 5 requirement). Clients MUST comply with the schema.
