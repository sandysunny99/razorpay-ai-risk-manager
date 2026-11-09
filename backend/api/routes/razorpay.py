"""Razorpay webhook adapter (works with Razorpay *test mode*).

Point a Razorpay Dashboard webhook (Settings → Webhooks) at
``POST /integrations/razorpay/webhook`` with the same secret as ``RAZORPAY_WEBHOOK_SECRET``.

Flow: verify ``X-Razorpay-Signature`` (HMAC-SHA256 of the raw body) → normalize the payment
entity into Netvrio's strict internal schema (opaque ids only; no card details, e-mail or phone
leave this function) → re-sign with the internal webhook secret → run the *same* protected
pipeline used by every other event, then publish to the live stream.
"""
import hashlib
import json
import os
import threading
import time

from fastapi import APIRouter, HTTPException, Request

from backend.api.routes.gateway_common import run_gateway_event
from backend.security.hmac import verify_hmac_sha256

router = APIRouter()

SUPPORTED_EVENTS = {"payment.authorized", "payment.captured", "payment.failed"}

_stats_lock = threading.Lock()
_stats = {"received": 0, "verified": 0, "rejected_signature": 0, "ignored": 0, "last_event_at": None}


def _bump(key: str) -> None:
    with _stats_lock:
        _stats[key] += 1
        _stats["last_event_at"] = int(time.time())


def _tenant() -> str:
    return os.getenv("RAZORPAY_TENANT_ID", "tenant_123")


def _pseudonymize(value: str) -> str:
    return "cust_h_" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def normalize_razorpay_event(body: dict, event_id_header: str | None, tenant_id: str) -> dict | None:
    """Map a Razorpay payment event onto the internal WebhookPayload schema, or None if unsupported."""
    event = body.get("event")
    if event not in SUPPORTED_EVENTS:
        return None
    entity = (((body.get("payload") or {}).get("payment") or {}).get("entity")) or {}
    payment_id = str(entity.get("id") or "unknown")[:60]

    customer = entity.get("customer_id")
    if not customer:
        contact = entity.get("email") or entity.get("contact")
        customer = _pseudonymize(str(contact)) if contact else "unknown"

    amount_paise = entity.get("amount")
    amount = round(amount_paise / 100.0, 2) if isinstance(amount_paise, (int, float)) else 0.0

    normalized = {
        "event_id": (event_id_header or f"rzp_{payment_id}_{event}")[:100],
        "timestamp": int(time.time()),  # Receipt time; Razorpay retries are de-duplicated by event id.
        "merchant_id": tenant_id,
        "event_type": event,
        "data": {
            "amount": amount,
            "currency": str(entity.get("currency") or "INR")[:3],
            "method": str(entity.get("method") or "unknown")[:20],
            "customer_id": str(customer)[:64],
            "gateway_status": str(entity.get("status") or "unknown")[:20],
            "gateway_payment_id": payment_id,
        },
    }
    token = entity.get("token_id") or entity.get("card_id")
    if token:
        normalized["token"] = str(token)[:255]
    return normalized


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="Razorpay webhook secret not configured")

    raw = await request.body()
    _bump("received")
    if not verify_hmac_sha256(secret, raw, request.headers.get("x-razorpay-signature", "")):
        _bump("rejected_signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    _bump("verified")

    try:
        body = json.loads(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail="Schema validation failed")

    tenant_id = _tenant()
    normalized = normalize_razorpay_event(body, request.headers.get("x-razorpay-event-id"), tenant_id)
    if normalized is None:
        _bump("ignored")
        return {"status": "ignored", "reason": "unsupported event type"}

    return run_gateway_event(normalized, tenant_id, request, source="razorpay", scenario=normalized["event_type"])


@router.get("/status")
def razorpay_status():
    with _stats_lock:
        stats = dict(_stats)
    return {
        "configured": bool(os.getenv("RAZORPAY_WEBHOOK_SECRET")),
        "tenant_id": _tenant(),
        "webhook_path": "/integrations/razorpay/webhook",
        "supported_events": sorted(SUPPORTED_EVENTS),
        **stats,
    }
