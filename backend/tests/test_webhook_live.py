"""
Live Razorpay Webhook Receiver Unit Tests
"""
import hashlib
import hmac
import json

from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _generate_test_signature(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def test_live_webhook_payment_captured_success(client):
    """Valid webhook HMAC signature is accepted with 200 OK and background processing."""
    secret = "ci_test_hmac_secret_key_only_for_testing_2026"
    payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_live_test_1001",
                    "amount": 1850000,
                    "currency": "INR",
                    "status": "captured",
                }
            }
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = _generate_test_signature(raw_body, secret)

    response = client.post(
        "/api/v1/razorpay/webhook",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["event"] == "payment.captured"
    assert data["processed"] is True


def test_live_webhook_invalid_signature_rejected(client):
    """Invalid webhook signature triggers HTTP 401 Unauthorized in production mode."""
    payload = {"event": "payment.captured", "payload": {}}
    raw_body = json.dumps(payload).encode("utf-8")

    response = client.post(
        "/api/v1/razorpay/webhook",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": "bad_signature_hex"},
    )
    assert response.status_code == 401


def test_live_webhook_dispute_and_token_events(client):
    """Dispute and token expired events are accepted and routed cleanly."""
    secret = "ci_test_hmac_secret_key_only_for_testing_2026"
    events = ["payment.dispute.created", "token.expired", "payment.failed"]

    for ev in events:
        payload = {"event": ev, "payload": {}}
        raw_body = json.dumps(payload).encode("utf-8")
        sig = _generate_test_signature(raw_body, secret)

        response = client.post(
            "/api/v1/razorpay/webhook",
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
        )
        assert response.status_code == 200
        assert response.json()["event"] == ev
