import hashlib
import hmac
import json
import time
import uuid

from fastapi.testclient import TestClient
import pytest

from backend.api.app import app

client = TestClient(app)

def sign_payload(payload_dict):
    body = json.dumps(payload_dict).encode('utf-8')
    sig = hmac.new(b"dummy_webhook_secret", body, hashlib.sha256).hexdigest()
    return body, sig

def test_audit_api_tenant_isolation():
    # 1. Create a webhook for Tenant A
    now = int(time.time())
    u = str(uuid.uuid4())[:8]
    payload = {"event_id": f"aud_iso_{u}", "timestamp": now, "merchant_id": "t_A", "token": "tok_123"}
    body, sig = sign_payload(payload)

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t_A"})
    assert resp.status_code == 200
    audit_id = resp.json()["audit_id"]

    # 2. Access Audit as Tenant A -> Success
    resp_a = client.get(f"/audit/{audit_id}", headers={"x-tenant-id": "t_A"})
    assert resp_a.status_code == 200
    assert "chain_verified" in resp_a.json()
    assert "raw_payload" not in resp_a.json()

    # 3. Access Audit as Tenant B -> 404 (Isolation)
    resp_b = client.get(f"/audit/{audit_id}", headers={"x-tenant-id": "t_B"})
    assert resp_b.status_code == 404
