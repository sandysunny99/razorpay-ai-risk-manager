"""YouPI-PG adapter (self-hosted UPI gateway, https://github.com/youpi-pg/YouPI-PG).

YouPI-PG describes itself as experimental and not NPCI/RBI/bank approved. Its OBSERVED_SUCCESS
events come from parsing bank alerts (SMS / e-mail) and are NOT settlement proof; only RECONCILED
(statement-matched) events are. Netvrio scores both but labels observed-only payments as
unreconciled so nothing downstream treats them as settled.

Verification follows the project's documented scheme: X-Gateway-Signature is "sha256=" + hex
HMAC-SHA256 of the raw body; X-Gateway-Signature-V2 binds "<timestamp_ms>.<raw body>". V2 is
checked whenever present and required when YOUPI_REQUIRE_V2=true. Retries reuse
X-Gateway-Delivery-Id for up to an hour, so de-duplication keys on it and freshness allows 2 hours.
"""
import hashlib
import hmac
import json
import os
import threading
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from backend.api.ratelimit import ingest_limit, limiter
from backend.api.routes.gateway_common import run_gateway_event

router = APIRouter()

SUPPORTED_EVENTS = {"OBSERVED_SUCCESS", "RECONCILED"}
MAX_AGE_MS = 2 * 3600 * 1000

_lock = threading.Lock()
_stats = {"received": 0, "verified": 0, "rejected_signature": 0, "ignored": 0, "duplicates": 0, "last_event_at": None}


def _bump(key: str) -> None:
    with _lock:
        _stats[key] += 1
        _stats["last_event_at"] = int(time.time())


def _sign(secret: bytes, msg: bytes) -> str:
    return "sha256=" + hmac.new(secret, msg, hashlib.sha256).hexdigest()


def normalize_youpi_event(body: dict, delivery_id: str, tenant_id: str) -> Optional[dict]:
    event = str(body.get("event") or "").upper()
    if event not in SUPPORTED_EVENTS:
        return None
    paise = body.get("amountPaise")
    if isinstance(paise, int):
        amount = round(paise / 100.0, 2)
    else:
        try:
            amount = round(float(body.get("amount")), 2)
        except (TypeError, ValueError):
            amount = 0.0
    payer = body.get("payerVpa") or body.get("vpa")
    customer = "cust_h_" + hashlib.sha256(str(payer).encode()).hexdigest()[:16] if payer else "unknown"
    utr = str(body.get("utr") or "")
    settlement = str(body.get("settlementState") or "NOT_RECONCILED").upper()
    return {
        "event_id": f"youpi_{delivery_id}"[:100],
        "timestamp": int(time.time()),
        "merchant_id": tenant_id,
        "event_type": f"upi.{event.lower()}",
        "data": {
            "amount": amount,
            "currency": "INR",
            "method": "upi",
            "customer_id": customer,
            "settlement_state": settlement[:20],
            "reconciled": settlement == "RECONCILED" and event == "RECONCILED",
            "utr_last4": utr[-4:] if utr else None,
            "gateway_order_id": str(body.get("orderId") or "")[:64],
        },
    }


@router.post("/webhook")
@limiter.limit(ingest_limit)
async def youpi_webhook(request: Request):
    secret = os.getenv("YOUPI_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="YouPI webhook secret not configured")
    raw = await request.body()
    _bump("received")
    key = secret.encode("utf-8")
    ts = request.headers.get("x-gateway-timestamp", "")
    v1 = request.headers.get("x-gateway-signature", "")
    v2 = request.headers.get("x-gateway-signature-v2")
    require_v2 = os.getenv("YOUPI_REQUIRE_V2", "false").lower() == "true"

    ok = hmac.compare_digest(v1, _sign(key, raw))
    if ok and (v2 is not None or require_v2):
        ok = v2 is not None and hmac.compare_digest(v2, _sign(key, ts.encode() + b"." + raw))
    if not ok:
        _bump("rejected_signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    if not ts.isdigit() or abs(time.time() * 1000 - int(ts)) > MAX_AGE_MS:
        _bump("rejected_signature")
        raise HTTPException(status_code=401, detail="Replay or stale timestamp detected")
    _bump("verified")

    try:
        body = json.loads(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail="Schema validation failed") from None
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Schema validation failed")
    delivery_id = request.headers.get("x-gateway-delivery-id") or str(body.get("deliveryId") or "")
    if not delivery_id:
        raise HTTPException(status_code=400, detail="Schema validation failed")

    tenant_id = os.getenv("YOUPI_TENANT_ID", "tenant_123")
    normalized = normalize_youpi_event(body, delivery_id, tenant_id)
    if normalized is None:
        _bump("ignored")
        return {"status": "ignored", "reason": "unsupported event type"}
    response = run_gateway_event(normalized, tenant_id, request, source="youpi", scenario=normalized["event_type"])
    if b'"duplicate"' in response.body:
        _bump("duplicates")
    return response


@router.get("/status")
def youpi_status():
    with _lock:
        stats = dict(_stats)
    return {
        "configured": bool(os.getenv("YOUPI_WEBHOOK_SECRET")),
        "require_v2": os.getenv("YOUPI_REQUIRE_V2", "false").lower() == "true",
        "tenant_id": os.getenv("YOUPI_TENANT_ID", "tenant_123"),
        "webhook_path": "/integrations/youpi/webhook",
        "supported_events": sorted(SUPPORTED_EVENTS),
        "experimental": True,
        **stats,
    }
