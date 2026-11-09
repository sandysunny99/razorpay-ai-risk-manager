import hashlib
import hmac
import json
import os
import time
import uuid

from fastapi.testclient import TestClient
import pytest

from backend.api.app import app

client = TestClient(app)

def sign_payload(payload_dict, secret="dummy_webhook_secret"):
    body = json.dumps(payload_dict).encode('utf-8')
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return body, sig

def test_missing_webhook_secret_fails(monkeypatch):
    monkeypatch.setenv("NETVRIO_ENV", "production")
    if "WEBHOOK_SECRET" in os.environ:
        monkeypatch.delenv("WEBHOOK_SECRET")

    payload = {"event_id": "1", "timestamp": int(time.time()), "merchant_id": "t1", "data": {}}
    body, sig = sign_payload(payload)
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t1"})
    assert resp.status_code == 501
    assert "Production authentication not configured" in resp.json()["detail"]

def test_production_tenant_auth_fails_unconfigured(monkeypatch):
    monkeypatch.setenv("NETVRIO_TENANT_AUTH_MODE", "JWT")
    monkeypatch.setenv("NETVRIO_ENV", "production")

    # We must reload dependencies or bypass the singleton to test it,
    # but simplest is just checking the provider instantiation
    from backend.api.dependencies import get_tenant_auth_provider
    provider = get_tenant_auth_provider()
    # It returns ProductionTenantAuthProvider which raises 501
    with pytest.raises(Exception) as exc:
        class MockReq:
            headers = {}
        provider.authenticate(MockReq())
    assert "Production authentication not configured" in str(exc.value)

def test_security_headers():
    resp = client.get("/health")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

def test_cors_rejection(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://trusted.netvrio.com")
    monkeypatch.setenv("NETVRIO_ENV", "production")

    # Reload app to capture new CORS settings
    import importlib

    from backend.api import app as my_app
    importlib.reload(my_app)

    local_client = TestClient(my_app.app)

    # Trusted
    resp_trusted = local_client.options("/webhooks/payment", headers={"Origin": "https://trusted.netvrio.com", "Access-Control-Request-Method": "POST"})
    assert resp_trusted.status_code == 200
    assert resp_trusted.headers.get("access-control-allow-origin") == "https://trusted.netvrio.com"

    # Untrusted
    resp_untrusted = local_client.options("/webhooks/payment", headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "POST"})
    assert resp_untrusted.status_code == 400
    # In Starlette CORS, if it's not allowed, it doesn't return the access-control-allow-origin header
    assert "access-control-allow-origin" not in resp_untrusted.headers or resp_untrusted.headers.get("access-control-allow-origin") == "https://trusted.netvrio.com"


def test_pydantic_webhook_validation():
    now = int(time.time())

    # Missing required field `merchant_id`
    bad_payload = {"event_id": "v1", "timestamp": now, "data": {}}
    body, sig = sign_payload(bad_payload)
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t1"})
    assert resp.status_code in (200, 400)
    assert "Schema validation failed" in resp.json()["detail"]

def test_telemetry_span_export_leakage():
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from backend.observability.tracing import add_span_processor

    memory_exporter = InMemorySpanExporter()
    add_span_processor(SimpleSpanProcessor(memory_exporter))

    now = int(time.time())
    u = str(uuid.uuid4())[:8]
    payload = {
        "event_id": f"evt_leak_{u}",
        "timestamp": now,
        "merchant_id": "t1",
        "data": {
            "pan": "4111999988887777",
            "cvv": "999",
            "api_key": "sk_live_verysecret"
        }
    }
    body, sig = sign_payload(payload)
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t1"})

    # It should fail with 400 because of raw pan rejection, which is fine, but spans are still emitted!
    assert resp.status_code in (200, 400)

    spans = memory_exporter.get_finished_spans()
    assert len(spans) > 0

    # Assert NO span attribute or event contains the sensitive strings
    for span in spans:
        for key, val in span.attributes.items():
            val_str = str(val)
            assert "4111999988887777" not in val_str
            assert "999" not in val_str
            assert "sk_live_verysecret" not in val_str

    memory_exporter.clear()
