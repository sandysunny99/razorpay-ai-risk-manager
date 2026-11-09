
import hashlib
import hmac
import json
import os
import time
import uuid

from fastapi.testclient import TestClient
import pytest

# Must ensure test setup
os.environ['NETVRIO_ENV'] = 'test'
os.environ['NETVRIO_DEMO_MODE'] = 'true'
os.environ['WEBHOOK_SECRET'] = 'dummy_webhook_secret'
os.environ['AUDIT_DB_URL'] = 'sqlite:///netvrio_audit.db'

from backend.api.app import app

client = TestClient(app)
WEBHOOK_SECRET = "dummy_webhook_secret"

def sign_payload(payload_dict):
    body = json.dumps(payload_dict).encode('utf-8')
    sig = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return body, sig

def test_e2e_a_valid_synthetic_transaction():
    event_id = f"e2e_valid_{str(uuid.uuid4())[:8]}"
    payload = {
        "event_id": event_id,
        "timestamp": int(time.time()),
        "merchant_id": "tenant_123",
        "data": {"amount": 500, "currency": "USD"}
    }
    body, sig = sign_payload(payload)

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "tenant_123"})
    assert resp.status_code == 200

    data = resp.json()
    assert "decision" in data
    assert data["decision"] in ["ALLOW", "REVIEW", "BLOCK", "QUARANTINE"]
    assert "audit_id" in data
    assert "correlation_id" in data
    assert "card_pan" not in data
    assert "cvv" not in data
    assert data["correlation_id"] == resp.headers.get("x-correlation-id")

def test_e2e_b_invalid_hmac():
    event_id = f"e2e_invalid_{str(uuid.uuid4())[:8]}"
    payload = {
        "event_id": event_id,
        "timestamp": int(time.time()),
        "merchant_id": "tenant_123"
    }
    body, _ = sign_payload(payload)

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": "bad_sig", "x-tenant-id": "tenant_123"})
    assert resp.status_code == 401

    data = resp.json()
    assert "detail" in data
    assert "card_pan" not in data
    # Idempotency is NOT consumed, meaning it was rejected before business processing

def test_e2e_c_replay_validation():
    event_id = f"e2e_replay_{str(uuid.uuid4())[:8]}"
    payload = {
        "event_id": event_id,
        "timestamp": int(time.time()) - 1000, # 1000 seconds ago
        "merchant_id": "tenant_123"
    }
    body, sig = sign_payload(payload)
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "tenant_123"})
    assert resp.status_code == 401
    assert "Replay" in resp.json()["detail"] or "Timestamp" in resp.json()["detail"]

def test_e2e_d_duplicate_event_idempotency():
    event_id = f"e2e_dup_{str(uuid.uuid4())[:8]}"
    payload = {
        "event_id": event_id,
        "timestamp": int(time.time()),
        "merchant_id": "tenant_123"
    }
    body, sig = sign_payload(payload)

    resp1 = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "tenant_123"})
    assert resp1.status_code == 200

    resp2 = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "tenant_123"})
    assert resp2.status_code == 401 # Duplicate rejected

def test_e2e_e_raw_pan_injection():
    event_id = f"e2e_pan_{str(uuid.uuid4())[:8]}"
    payload = {
        "event_id": event_id,
        "timestamp": int(time.time()),
        "merchant_id": "tenant_123",
        "card_pan": "4111222233334444"
    }
    body, sig = sign_payload(payload)

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "tenant_123"})
    assert resp.status_code == 400

    # Must not leak PAN in error
    assert "4111222233334444" not in resp.text

def test_e2e_f_cross_tenant_merchant_mismatch():
    event_id = f"e2e_mismatch_{str(uuid.uuid4())[:8]}"
    payload = {
        "event_id": event_id,
        "timestamp": int(time.time()),
        "merchant_id": "merchant_B" # Payload says B
    }
    body, sig = sign_payload(payload)

    # But authenticated as A
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "tenant_A"})
    assert resp.status_code == 403
    assert "Tenant mismatch" in resp.json()["detail"]

def test_e2e_phase11_audit_chain():
    event_id = f"e2e_audit_{str(uuid.uuid4())[:8]}"
    payload = {
        "event_id": event_id,
        "timestamp": int(time.time()),
        "merchant_id": "tenant_123",
        "data": {"amount": 100}
    }
    body, sig = sign_payload(payload)
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "tenant_123"})
    assert resp.status_code == 200

    audit_id = resp.json()["audit_id"]

    # Fetch audit
    audit_resp = client.get(f"/audit/{audit_id}", headers={"x-tenant-id": "tenant_123"})
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()

    assert audit_data["audit_id"] == audit_id
    assert audit_data["chain_verified"] is True
    assert audit_data["event_id"] == event_id

    # Wrong tenant fetches audit
    audit_resp_wrong = client.get(f"/audit/{audit_id}", headers={"x-tenant-id": "tenant_wrong"})
    assert audit_resp_wrong.status_code == 404

def test_e2e_phase5_unexpected_fields():
    event_id = f"e2e_extra_{str(uuid.uuid4())[:8]}"
    payload = {
        "event_id": event_id,
        "timestamp": int(time.time()),
        "merchant_id": "tenant_123",
        "sneaky_field": "123"
    }
    body, sig = sign_payload(payload)
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "tenant_123"})
    assert resp.status_code == 400 # Pydantic Validation Error because of extra='forbid'
