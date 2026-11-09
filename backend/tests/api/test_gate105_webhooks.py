import os
import uuid

os.environ['NETVRIO_ENV'] = 'test'
os.environ['NETVRIO_DEMO_MODE'] = 'true'
os.environ['WEBHOOK_SECRET'] = 'dummy_webhook_secret'
import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient
import pytest

from backend.api.app import app

client = TestClient(app)
WEBHOOK_SECRET = "dummy_webhook_secret"

def sign_payload(payload_dict):
    body = json.dumps(payload_dict).encode('utf-8')
    sig = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return body, sig

def test_webhook_e2e_valid():
    now = int(time.time())
    payload = {"event_id": f"e2e_valid_1_{str(uuid.uuid4())[:8]}", "timestamp": now, "merchant_id": "t1"}
    body, sig = sign_payload(payload)

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] in ["ALLOW", "REVIEW", "BLOCK", "QUARANTINE"]
    assert "audit_id" in data

    # Check duplicate
    resp2 = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t1"})
    assert resp2.status_code == 401 # Duplicate rejected

def test_webhook_e2e_invalid_signature():
    now = int(time.time())
    payload = {"event_id": f"e2e_invalid_sig_{str(uuid.uuid4())[:8]}", "timestamp": now, "merchant_id": "t1"}
    body, _ = sign_payload(payload) # Ignore real sig

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": "bad_sig", "x-tenant-id": "t1"})
    assert resp.status_code == 401

    # Prove idempotency was NOT consumed by sending with valid signature now
    body2, sig2 = sign_payload(payload)
    resp2 = client.post("/webhooks/payment", content=body2, headers={"x-signature": sig2, "x-tenant-id": "t1"})
    assert resp2.status_code == 200 # Accepted!

def test_webhook_e2e_stale_timestamp():
    payload = {"event_id": f"e2e_stale_{str(uuid.uuid4())[:8]}", "timestamp": int(time.time()) - 1000, "merchant_id": "t1"}
    body, sig = sign_payload(payload)
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t1"})
    assert resp.status_code == 401

def test_webhook_e2e_tenant_isolation():
    now = int(time.time())
    payload = {"event_id": f"e2e_cross_tenant_{str(uuid.uuid4())[:8]}", "timestamp": now, "merchant_id": "t_A"}
    body, sig = sign_payload(payload)

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t_A"})
    assert resp.status_code == 200

    # Same event, different tenant -> must fail because of tenant mismatch payload (payload has merchant_id t_A, but header is t_B)
    resp2 = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t_B"})
    assert resp2.status_code == 403 # Rejected!
