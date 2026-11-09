import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient
import pytest

from backend.api.app import app

client = TestClient(app)

def test_sensitive_data_does_not_leak_in_api():
    payload = {
        "event_id": "evt_sensitive",
        "timestamp": int(time.time()),
        "merchant_id": "t1",
        "card_pan": "4111222233334444",
        "cvv": "999",
        "nested": {"authorization": "Bearer MY_SECRET_TOKEN"}
    }
    body = json.dumps(payload).encode('utf-8')
    sig = hmac.new(b"dummy_webhook_secret", body, hashlib.sha256).hexdigest()

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "t1"})

    resp_text = resp.text
    # Ensure sensitive fields do NOT appear in the API response output
    assert "4111222233334444" not in resp_text
    assert "999" not in resp_text
    assert "MY_SECRET_TOKEN" not in resp_text
