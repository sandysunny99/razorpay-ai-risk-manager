import hashlib
import hmac
import json
import time
import uuid

from fastapi.testclient import TestClient
import pytest

from backend.api.app import app

client = TestClient(app)
WEBHOOK_SECRET = "dummy_webhook_secret"

def sign_payload(payload_dict):
    body = json.dumps(payload_dict).encode('utf-8')
    sig = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return body, sig

def test_raw_pan_rejected_by_zombie_saver():
    now = int(time.time())
    u = str(uuid.uuid4())[:8]
    # Provide raw card_pan without token to trigger ZombieSaver rejection
    payload = {"event_id": f"raw_pan_{u}", "timestamp": now, "merchant_id": "t1", "card_pan": "4111222233334444"}
    body, sig = sign_payload(payload)

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t1"})
    # Zombie card saver raises ValueError -> 400
    assert resp.status_code == 400
    assert "Raw account numbers" in resp.json()["detail"] or "PAN" in resp.json()["detail"] or "Raw reference not permitted" in resp.json()["detail"]

def test_token_accepted_by_zombie_saver():
    now = int(time.time())
    u = str(uuid.uuid4())[:8]
    # Provide a safe token
    payload = {"event_id": f"token_{u}", "timestamp": now, "merchant_id": "t1", "token": "tok_123"}
    body, sig = sign_payload(payload)

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t1"})
    assert resp.status_code == 200
