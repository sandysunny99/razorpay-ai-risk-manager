"""Shared path for payment-gateway adapters (Razorpay, YouPI-PG).

After the adapter has verified the gateway's own signature and normalized the event, this
re-signs it with the internal secret and runs the single protected pipeline. Gateways retry
deliveries they think failed, so a delivery that was already processed is acknowledged with
200 "duplicate" instead of an error (an error would make the gateway retry for up to an hour).
"""
import hashlib
import hmac
import json
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.api.dependencies import get_webhook_secret
from backend.api.routes.webhooks import process_and_publish
from backend.security.idempotency import get_idempotency_store


def run_gateway_event(normalized: dict, tenant_id: str, request: Request, source: str, scenario: str) -> JSONResponse:
    if get_idempotency_store().has_seen(normalized["event_id"], tenant_id):
        return JSONResponse({"status": "duplicate", "event_id": normalized["event_id"]})
    internal_secret = get_webhook_secret()
    body = json.dumps(normalized, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(internal_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    correlation_id = getattr(request.state, "correlation_id", f"corr_{uuid.uuid4()}")
    result = process_and_publish(body, sig, tenant_id, internal_secret, correlation_id, source=source, scenario=scenario)
    return JSONResponse(result)
