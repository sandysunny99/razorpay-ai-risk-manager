import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security.encryption import FieldEncryptionEngine
from app.security.key_provider import key_provider
from app.security.masking import (
    mask_pan, mask_email, mask_phone, mask_ip, mask_customer_id,
    mask_token, mask_api_key, mask_jwt, mask_cloudflare_ray_id, MaskingPolicy
)
from app.security.dlp import DLPEngine
from app.integrations.cloudflare_adapter import cloudflare_adapter

client = TestClient(app)

def test_field_encryption_and_decryption_aes256_gcm():
    plaintext = "sensitive_cardholder_data_4921"
    encrypted = FieldEncryptionEngine.encrypt(plaintext)
    
    assert "ciphertext" in encrypted
    assert "nonce" in encrypted
    assert encrypted["algorithm"] == "AES-256-GCM"
    assert encrypted["key_version"] == "v1"
    assert encrypted["ciphertext"] != plaintext

    decrypted = FieldEncryptionEngine.decrypt(encrypted)
    assert decrypted == plaintext

def test_field_encryption_tamper_detection():
    plaintext = "secret_transaction_payload"
    encrypted = FieldEncryptionEngine.encrypt(plaintext)
    
    # Tamper with base64 ciphertext
    tampered = dict(encrypted)
    tampered["ciphertext"] = "AAAA" + tampered["ciphertext"][4:]
    
    with pytest.raises(ValueError, match="Decryption failed"):
        FieldEncryptionEngine.decrypt(tampered)

def test_key_provider_rotation_and_safe_metadata():
    active_key = key_provider.get_active_key()
    assert active_key["version"] == "v1"

    # Rotate key
    new_key = key_provider.rotate_key()
    assert new_key["version"] == "v2"
    assert new_key["status"] == "ACTIVE"

    # Check safe metadata (must NOT contain raw key_bytes)
    meta = key_provider.get_all_key_metadata()
    assert len(meta) >= 2
    for m in meta:
        assert "key_bytes" not in m
        assert "version" in m
        assert "status" in m

def test_dynamic_masking_primitives():
    assert mask_pan("4111 1111 1111 4921") == "**** **** **** 4921"
    assert mask_email("alice.wonderland@razorpay.com") == "a***d@razorpay.com"
    assert mask_phone("+919876543210") == "+** ******3210"
    assert mask_ip("122.166.45.10") == "122.166.***.***"
    assert mask_customer_id("cust_544192") == "cust_***192"
    assert mask_token("tok_live_98765432") == "tok_***5432"
    assert mask_api_key("rzp_live_9a8b7c6d5e") == "rzp_***d5e"
    assert "MASKED_JWT" in mask_jwt("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc")
    assert mask_cloudflare_ray_id("8c41f0a12e9b") == "8c41...2e9b"

def test_masking_policy_role_enforcement():
    data = {
        "pan": "4111111111114921",
        "email": "user@test.com",
        "ip_address": "192.168.1.100"
    }
    masked = MaskingPolicy.apply(data, role="ANALYST")
    assert masked["masked_pan"] == "**** **** **** 4921"
    assert "pan" not in masked
    assert "***" in masked["email"]
    assert "***" in masked["ip_address"]

def test_dlp_engine_luhn_pan_and_secret_detection():
    sample_text = (
        "User 4111 1111 1111 1111 attempted login with Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.def "
        "and API key rzp_live_9a8b7c6d5e using postgresql://admin:secret@db:5432/risk"
    )
    violations = DLPEngine.scan_for_violations(sample_text)
    v_types = [v["type"] for v in violations]
    
    assert "PAN_DETECTED" in v_types
    assert "JWT_TOKEN_DETECTED" in v_types
    assert "API_KEY_DETECTED" in v_types
    assert "DB_CONNECTION_DETECTED" in v_types

    redacted = DLPEngine.redact(sample_text)
    assert "4111 1111 1111 1111" not in redacted
    assert "**** **** **** 1111" in redacted
    assert "[REDACTED_JWT]" in redacted
    assert "[REDACTED_API_KEY]" in redacted
    assert "[REDACTED_DB_URI]" in redacted

def test_cloudflare_adapter_normalization():
    headers = {
        "cf-ray": "8c41f0a12e9b",
        "cf-ipcountry": "US",
        "cf-connecting-ip": "198.51.100.25"
    }
    event = cloudflare_adapter.normalize_security_event(
        headers=headers,
        event_type="WAF_INSPECT",
        waf_action="ALLOW",
        bot_score=15,  # Bot score < 30
        rate_limit_action="ALLOW"
    )
    assert event["country"] == "US"
    assert event["bot_signal"] == "AUTOMATED_BOT_SUSPECTED"
    assert event["tls_version"] == "TLSv1.3"
    assert "masked_ray_id" in event

def test_security_and_health_api_endpoints():
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "healthy"

    r2 = client.get("/api/v1/health/dependencies")
    assert r2.status_code == 200
    assert r2.json()["dependencies"]["sqlite_database"] == "UP"
    assert r2.json()["dependencies"]["cloudflare_edge_adapter"] == "UP"

    r3 = client.get("/api/v1/security/data-protection")
    assert r3.status_code == 200
    assert r3.json()["data_at_rest"]["status"] == "PASS"
    assert r3.json()["data_in_transit"]["status"] == "PASS"

    r4 = client.post("/api/v1/security/dlp/test", json={"input_text": "Payment with card 4111 1111 1111 1111"})
    assert r4.status_code == 200
    assert r4.json()["violations_detected"] >= 1
    assert "**** **** **** 1111" in r4.json()["sanitized_output"]

def test_exposure_api_endpoints():
    r1 = client.get("/api/v1/exposure/statistics")
    assert r1.status_code == 200
    assert "cards_monitored" in r1.json()

    r2 = client.get("/api/v1/exposure/events")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)
