import hashlib
import hmac
import json
import time
import uuid

from fastapi.testclient import TestClient
import pytest

from backend.api.app import app
from backend.observability.sanitizer import sanitize_telemetry

client = TestClient(app)

def test_telemetry_sanitizer():
    dirty = {
        "pan": "4111222233334444",
        "nested": {
            "cvv": "123",
            "api_key": "sk_live_123"
        },
        "safe_field": "hello"
    }
    clean = sanitize_telemetry(dirty)
    assert clean["pan"] == "[REDACTED]"
    assert clean["nested"]["cvv"] == "[REDACTED]"
    assert clean["nested"]["api_key"] == "[REDACTED]"
    assert clean["safe_field"] == "hello"

def test_observability_headers_and_payload_size():
    # Test large payload rejection
    large_payload = "A" * (1024 * 1024 + 10)
    resp = client.post("/webhooks/payment", content=large_payload, headers={"x-signature": "dummy", "x-tenant-id": "t1"})
    assert resp.status_code == 413

    # Test valid correlation ID propagation
    now = int(time.time())
    u = str(uuid.uuid4())[:8]
    payload = {"event_id": f"obs_{u}", "timestamp": now, "merchant_id": "t_A", "token": "tok_123"}
    body = json.dumps(payload).encode('utf-8')
    sig = hmac.new(b"dummy_webhook_secret", body, hashlib.sha256).hexdigest()

    my_corr_id = "corr_custom_123"
    resp2 = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t_A", "x-correlation-id": my_corr_id})
    assert resp2.status_code == 200

    assert resp2.headers.get("x-correlation-id") == my_corr_id
    assert resp2.json()["correlation_id"] == my_corr_id
