import hashlib
import hmac
import json
import os
import time
import uuid

from fastapi.testclient import TestClient

os.environ["WEBHOOK_SECRET"] = "dummy_webhook_secret"

from backend.api.app import app  # noqa: E402

client = TestClient(app)


def _post(tenant: str, data: dict) -> dict:
    payload = {"event_id": f"evt_L_{uuid.uuid4().hex[:8]}", "merchant_id": tenant, "timestamp": int(time.time()), "data": data}
    body = json.dumps(payload).encode()
    sig = hmac.new(b"dummy_webhook_secret", body, hashlib.sha256).hexdigest()
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": tenant})
    assert resp.status_code == 200
    return resp.json()


def test_list_is_tenant_scoped_and_metadata_only():
    tenant_a = f"t_list_a_{uuid.uuid4().hex[:6]}"
    tenant_b = f"t_list_b_{uuid.uuid4().hex[:6]}"
    res_a = _post(tenant_a, {"amount": 100, "note": "customer said hi"})
    _post(tenant_b, {"amount": 120000})

    items = client.get("/audit", headers={"x-tenant-id": tenant_a}).json()["items"]
    assert [i["audit_id"] for i in items] == [res_a["audit_id"]]
    item = items[0]
    assert item["decision"] == "ALLOW"
    assert item["risk_level"] == "LOW"
    assert "record_payload" not in item
    assert "customer said hi" not in json.dumps(item)


def test_list_requires_tenant_header():
    assert client.get("/audit").status_code == 401


def test_summary_counts_decisions():
    tenant = f"t_sum_{uuid.uuid4().hex[:6]}"
    _post(tenant, {"amount": 100})
    _post(tenant, {"amount": 120000})
    _post(tenant, {"amount": 100, "card_lifecycle": "EXPIRED", "recent_reuse_count": 6})

    summary = client.get("/audit/summary", headers={"x-tenant-id": tenant}).json()
    assert summary["total"] == 3
    assert summary["decisions"]["ALLOW"] == 1
    assert summary["decisions"]["BLOCK"] == 1
    assert summary["zombie_detected"] == 1
    assert summary["chain_verified"] is True


def test_raw_pan_does_not_consume_event_id():
    tenant = f"t_pan_{uuid.uuid4().hex[:6]}"
    event_id = f"evt_P_{uuid.uuid4().hex[:8]}"
    pan = "4111" + "1111" + "1111" + "1111"
    base = {"event_id": event_id, "merchant_id": tenant, "timestamp": int(time.time()), "data": {"amount": 100}}

    bad = json.dumps({**base, "card_pan": pan}).encode()
    sig = hmac.new(b"dummy_webhook_secret", bad, hashlib.sha256).hexdigest()
    assert client.post("/webhooks/payment", content=bad, headers={"x-signature": sig, "x-tenant-id": tenant}).status_code == 400

    # The rejected PAN request must not have registered the event id.
    good = json.dumps(base).encode()
    sig = hmac.new(b"dummy_webhook_secret", good, hashlib.sha256).hexdigest()
    assert client.post("/webhooks/payment", content=good, headers={"x-signature": sig, "x-tenant-id": tenant}).status_code == 200


def test_demo_signed_body_verifies_verbatim(monkeypatch):
    monkeypatch.setenv("NETVRIO_DEMO_MODE", "true")
    monkeypatch.setenv("NETVRIO_ENV", "test")
    tenant = f"t_sig_{uuid.uuid4().hex[:6]}"
    payload = {"event_id": f"evt_S_{uuid.uuid4().hex[:8]}", "merchant_id": tenant, "timestamp": int(time.time()),
               "data": {"amount": 100}}
    signed = client.post("/webhooks/demo/sign", json=payload).json()
    # JS re-serialization of `payload` would render 100.0 as 100; the verbatim body must be used.
    assert '"amount":100.0' in signed["signed_body"]
    resp = client.post("/webhooks/payment", content=signed["signed_body"],
                       headers={"x-signature": signed["signature"], "x-tenant-id": tenant,
                                "content-type": "application/json"})
    assert resp.status_code == 200
