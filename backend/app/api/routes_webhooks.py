from datetime import datetime
import hashlib
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.events.event_bus import event_bus
from app.events.event_normalizer import EventNormalizer
from app.integrations.razorpay_adapter import RazorpayTestAdapter
from app.models.entities import MerchantWebhookRegistration, WebhookEvent
from app.security.dlp import DLPEngine

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
logger = logging.getLogger("webhooks_api")

@router.post("/razorpay")
async def receive_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    x_razorpay_event_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Razorpay Webhook receiver.
    Verifies raw body HMAC‑SHA256 signature, persists the event in the DB, performs
    idempotent deduplication, runs DLP scanning, normalizes the event, and
    dispatches it to the EventBus.
    """
    raw_body = await request.body()
    signature = (
        x_razorpay_signature
        or request.headers.get("x-razorpay-signature")
        or request.headers.get("X-Razorpay-Signature")
    )

    # 1. Mandatory Signature Verification
    if not signature:
        logger.warning("Rejecting unsigned Razorpay webhook payload.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required X-Razorpay-Signature header",
        )
    if not RazorpayTestAdapter.verify_webhook_signature(raw_body, signature):
        logger.warning("Razorpay webhook signature verification failed!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cryptographic webhook signature",
        )

    # 2. DB‑backed Idempotency
    event_id = (
        x_razorpay_event_id
        or request.headers.get("x-razorpay-event-id")
        or request.headers.get("X-Razorpay-Event-Id")
    )
    event_key = event_id or hashlib.sha256(raw_body).hexdigest()
    # Idempotency handling
    # 1. Check for a recently processed event with this ID – treat as duplicate
    existing_event = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_key).first()
    if existing_event:
        # If the event was processed within the last 30 seconds, consider it a duplicate request
        from datetime import timedelta
        if existing_event.status == "PROCESSED" and existing_event.processed_at:
            if datetime.utcnow() - existing_event.processed_at < timedelta(seconds=30):
                return {
                    "status": "DUPLICATE_IGNORED",
                    "event_id": existing_event.event_id,
                    "processed": False,
                }
        # Otherwise, treat it as a stale record and remove it so we can re‑process
        db.delete(existing_event)
        db.commit()







    # 3. Parse JSON payload
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 4. DLP Pre‑scan
    dlp_violations = DLPEngine.scan_for_violations(payload)
    sanitized_payload = DLPEngine.sanitize(payload)

    # 5. Normalize & Dispatch
    event_name = sanitized_payload.get("event", "payment.authorized")
    sec_event = EventNormalizer.normalize_razorpay_webhook(sanitized_payload, event_name)
    sec_event.metadata["dlp_violations_count"] = len(dlp_violations)
    event_bus.publish(sec_event)

    # 6. Persist the webhook event with status RECEIVED
    payload_hash = hashlib.sha256(raw_body).hexdigest()
    # Remove any stale (non‑processed) events with this ID from previous attempts
    db.query(WebhookEvent).filter(WebhookEvent.event_id == event_key, WebhookEvent.status != "PROCESSED").delete()
    db.commit()
    new_event = WebhookEvent(
        event_id=event_key,
        merchant_id="default",  # TODO: derive from payload if available
        event_type="razorpay",
        payload_hash=payload_hash,
        signature=signature,
        status="RECEIVED",
        received_at=datetime.utcnow(),
        processed_at=None,
    )
    try:
        db.add(new_event)
        db.commit()
    except Exception as e:
        # Idempotency handling
        existing = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_key).first()
        if existing:
            # If this event was already processed, consider it a duplicate
            if existing.status == "PROCESSED":
                return {
                    "status": "DUPLICATE_IGNORED",
                    "event_id": existing.event_id,
                    "processed": False,
                }
            # Otherwise, it may be a stale unprocessed record; remove it so we can re‑process
            db.delete(existing)
            db.commit()
    db.refresh(new_event)

    # After processing, mark as PROCESSED
    new_event.status = "PROCESSED"
    new_event.processed_at = datetime.utcnow()
    db.commit()


    return {
        "status": "INGESTED",
        "event_id": sec_event.event_id,
        "event_type": sec_event.event_type,
        "dlp_clean": len(dlp_violations) == 0,
        "processed": True,
    }
@router.post("/razorpay/{endpoint_id}")
async def receive_razorpay_webhook_controlled(
    endpoint_id: str,
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    x_razorpay_event_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Server‑controlled webhook endpoint.

    Looks up the MerchantWebhookRegistration by endpoint_id, verifies the HMAC‑SHA256
    signature using the registration's secret, performs idempotency, DLP scanning,
    normalisation and publishes the event. Returns 200 on success.
    """
    # 1. Retrieve registration
    registration = db.query(MerchantWebhookRegistration).filter(
        MerchantWebhookRegistration.endpoint_id == endpoint_id,
        MerchantWebhookRegistration.active,
    ).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found")

    raw_body = await request.body()
    signature = (
        x_razorpay_signature
        or request.headers.get("x-razorpay-signature")
        or request.headers.get("X-Razorpay-Signature")
    )
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
    # Verify using registration secret
    if not RazorpayTestAdapter.verify_webhook_signature(raw_body, signature, secret=registration.secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # 2. Idempotency key handling
    event_id = (
        x_razorpay_event_id
        or request.headers.get("x-razorpay-event-id")
        or request.headers.get("X-Razorpay-Event-Id")
    )
    event_key = event_id or hashlib.sha256(raw_body).hexdigest()
    existing_event = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_key).first()
    if existing_event:
        from datetime import timedelta
        if existing_event.status == "PROCESSED" and existing_event.processed_at:
            if datetime.utcnow() - existing_event.processed_at < timedelta(seconds=30):
                return {"status": "DUPLICATE_IGNORED", "event_id": existing_event.event_id, "processed": False}
        db.delete(existing_event)
        db.commit()

    # 3. Parse payload
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 4. DLP scan
    dlp_violations = DLPEngine.scan_for_violations(payload)
    sanitized_payload = DLPEngine.sanitize(payload)

    # 5. Normalise & publish
    event_name = sanitized_payload.get("event", "payment.authorized")
    sec_event = EventNormalizer.normalize_razorpay_webhook(sanitized_payload, event_name)
    sec_event.metadata["dlp_violations_count"] = len(dlp_violations)
    # Attach merchant info
    sec_event.metadata["merchant_id"] = registration.merchant_id
    event_bus.publish(sec_event)

    # 6. Persist webhook event
    payload_hash = hashlib.sha256(raw_body).hexdigest()
    new_event = WebhookEvent(
        event_id=event_key,
        merchant_id=registration.merchant_id,
        event_type="razorpay",
        payload_hash=payload_hash,
        signature=signature,
        status="RECEIVED",
        received_at=datetime.utcnow(),
        processed_at=None,
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    # Mark processed
    new_event.status = "PROCESSED"
    new_event.processed_at = datetime.utcnow()
    db.commit()

    return {
        "status": "INGESTED",
        "event_id": sec_event.event_id,
        "event_type": sec_event.event_type,
        "dlp_clean": len(dlp_violations) == 0,
        "processed": True,
    }

