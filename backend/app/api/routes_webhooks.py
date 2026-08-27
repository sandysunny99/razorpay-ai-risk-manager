import hashlib
import json
import logging
from typing import Optional
from fastapi import APIRouter, Request, Header, HTTPException, status
from app.integrations.razorpay_adapter import RazorpayTestAdapter
from app.events.event_normalizer import EventNormalizer
from app.events.event_deduplicator import event_deduplicator
from app.events.event_bus import event_bus
from app.security.dlp import DLPEngine
from app.core.security import verify_hmac_signature

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
logger = logging.getLogger("webhooks_api")

@router.post("/razorpay")
async def receive_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    x_razorpay_event_id: Optional[str] = Header(None)
):
    """
    Razorpay Webhook receiver.
    Verifies raw body HMAC-SHA256 signature, deduplicates event ID,
    scans with DLP, normalizes event, and dispatches to EventBus.
    """
    raw_body = await request.body()
    signature = x_razorpay_signature or request.headers.get("x-razorpay-signature") or request.headers.get("X-Razorpay-Signature")
    
    # 1. Mandatory Signature Verification
    if not signature:
        logger.warning("Rejecting unsigned Razorpay webhook payload.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required X-Razorpay-Signature header"
        )

    is_valid = RazorpayTestAdapter.verify_webhook_signature(raw_body, signature)
    if not is_valid:
        logger.warning("Razorpay webhook signature verification failed!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cryptographic webhook signature"
        )

    # 2. Idempotency Check (Provider Event ID or deterministic SHA-256 fallback)
    event_id = x_razorpay_event_id or request.headers.get("x-razorpay-event-id") or request.headers.get("X-Razorpay-Event-Id")
    event_key = event_id or hashlib.sha256(raw_body).hexdigest()
    if event_deduplicator.is_duplicate(event_key):
        return {
            "status": "DUPLICATE_IGNORED",
            "message": f"Event {event_key} already ingested and processed.",
            "processed": False
        }

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 3. DLP Pre-scan
    dlp_violations = DLPEngine.scan_for_violations(payload)
    sanitized_payload = DLPEngine.sanitize(payload)

    # 4. Normalize & Dispatch
    event_name = sanitized_payload.get("event", "payment.authorized")
    sec_event = EventNormalizer.normalize_razorpay_webhook(sanitized_payload, event_name)
    sec_event.metadata["dlp_violations_count"] = len(dlp_violations)
    
    event_bus.publish(sec_event)

    return {
        "status": "INGESTED",
        "event_id": sec_event.event_id,
        "event_type": sec_event.event_type,
        "dlp_clean": len(dlp_violations) == 0,
        "processed": True
    }
