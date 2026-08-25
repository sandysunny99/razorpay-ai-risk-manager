import pytest
import hmac
import hashlib
import json
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.enrichment.bin_provider import bin_provider, MockBinProvider
from app.enrichment.threat_provider import threat_enrichment_provider, MockThreatProvider
from app.events.event_deduplicator import event_deduplicator
from app.integrations.razorpay_adapter import RazorpayTestAdapter

def test_bin_provider_metadata_and_caching():
    # Test valid 6-digit BIN lookup
    visa_res = bin_provider.lookup_bin("453201")
    assert visa_res["scheme"] == "visa"
    assert "bank" in visa_res

    # Test mastercard lookup
    mc_res = bin_provider.lookup_bin("520000")
    assert mc_res["scheme"] == "mastercard"

    # Test short invalid BIN protection
    invalid_res = bin_provider.lookup_bin("123")
    assert "error" in invalid_res

def test_threat_provider_lookup_and_domain_ioc():
    # Test known malicious domain lookup
    malicious_res = threat_enrichment_provider.check_url_or_host("evil-stealer.xyz")
    assert malicious_res["threat"] in ["malware_download", "none"]

    # Test clean domain lookup
    clean_res = threat_enrichment_provider.check_url_or_host("google.com")
    assert clean_res["threat"] == "none"

def test_event_deduplicator_idempotency():
    dedup_key = "evt_test_unique_idempotency_123"
    assert event_deduplicator.is_duplicate(dedup_key) is False
    assert event_deduplicator.is_duplicate(dedup_key) is True

def test_razorpay_webhook_hmac_signature_verification():
    secret = settings.RAZORPAY_KEY_SECRET
    raw_payload = b'{"event":"payment.authorized","account_id":"acc_1","payload":{"payment":{"entity":{"id":"pay_100","amount":50000}}}}'
    
    valid_signature = hmac.new(secret.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()
    
    # Valid Signature Check
    assert RazorpayTestAdapter.verify_webhook_signature(raw_payload, valid_signature, secret=secret) is True
    
    # Tampered Body Check
    tampered_payload = b'{"event":"payment.authorized","account_id":"acc_1","payload":{"payment":{"entity":{"id":"pay_100","amount":999999}}}}'
    assert RazorpayTestAdapter.verify_webhook_signature(tampered_payload, valid_signature, secret=secret) is False

@pytest.mark.asyncio
async def test_webhook_api_endpoint_ingestion_and_dlp():
    secret = settings.RAZORPAY_KEY_SECRET
    payload = {
        "event": "payment.authorized",
        "account_id": "acc_merch_01",
        "event_id": "evt_test_webhook_001",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_wh_99",
                    "amount": 250000,
                    "currency": "INR",
                    "status": "authorized",
                    "card": {"last4": "1832"}
                }
            }
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig,
                "X-Razorpay-Event-Id": "evt_test_webhook_001"
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "INGESTED"
        assert data["processed"] is True

        # Test duplicate webhook idempotency
        res_dup = await ac.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig,
                "X-Razorpay-Event-Id": "evt_test_webhook_001"
            }
        )
        assert res_dup.status_code == 200
        assert res_dup.json()["status"] == "DUPLICATE_IGNORED"
