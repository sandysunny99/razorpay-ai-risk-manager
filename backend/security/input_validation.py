from typing import Any, Dict

from pydantic import BaseModel, Field


class WebhookEventPayload(BaseModel):
    """
    Validates the structure of an incoming webhook event.
    Rejects malformed or structurally invalid events.
    """
    event_id: str = Field(..., min_length=1)
    merchant_id: str = Field(..., min_length=1)
    timestamp: int = Field(...)
    event_type: str = Field(..., min_length=1)
    data: Dict[str, Any] = Field(..., min_length=1)
