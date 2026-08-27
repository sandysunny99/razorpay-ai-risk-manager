import hashlib
import hmac
import json
import os

import pytest

from app.services.razorpay_client import RazorpayTestClient


def test_razorpay_client_graceful_without_keys():
    """No API keys or mock keys -> available=False, no exceptions thrown."""
    client = RazorpayTestClient(key_id="", key_secret="")
    assert client.available is False
    assert client.create_test_order(50000) is None
    assert client.fetch_payment("pay_test") is None


def test_webhook_payload_generation_valid_hmac():
    """Generated HMAC signature accurately validates against the secret payload."""
    client = RazorpayTestClient(key_id="", key_secret="", webhook_secret="test_secret_12345")
    payload, signature = client.generate_test_webhook_payload("payment.captured")

    payload_str = json.dumps(payload, separators=(",", ":"))
    expected_sig = hmac.new(
        b"test_secret_12345", payload_str.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    assert signature == expected_sig


def test_webhook_payload_structure():
    """Generated webhook adheres to Razorpay event payload schema."""
    client = RazorpayTestClient(key_id="", key_secret="test_secret")
    payload, _ = client.generate_test_webhook_payload(
        "payment.captured", amount_paise=100000, card_last4="4242"
    )
    assert payload["entity"] == "event"
    assert "payment" in payload["contains"]
    entity = payload["payload"]["payment"]["entity"]
    assert entity["amount"] == 100000
    assert entity["card"]["last4"] == "4242"
    assert entity["status"] == "captured"


@pytest.mark.skipif(
    not os.getenv("RAZORPAY_KEY_ID", "").startswith("rzp_test_"),
    reason="No Razorpay live test key configured (requires real rzp_test_... in environment)",
)
def test_razorpay_live_test_order_creation():
    """Integration test against Razorpay test sandbox (only when live test keys present)."""
    key_id = os.environ["RAZORPAY_KEY_ID"]
    key_secret = os.environ["RAZORPAY_KEY_SECRET"]
    client = RazorpayTestClient(key_id=key_id, key_secret=key_secret)
    assert client.available is True
    order = client.create_test_order(5000)
    assert order is not None
    assert order["id"].startswith("order_")
    assert order["amount"] == 5000
    assert order["currency"] == "INR"
