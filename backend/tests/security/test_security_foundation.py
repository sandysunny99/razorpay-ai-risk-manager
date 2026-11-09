import hashlib
import hmac
import time

import pytest

from backend.security.dlp import redact_sensitive_data
from backend.security.hmac import verify_hmac_sha256
from backend.security.idempotency import InMemoryIdempotencyStore
from backend.security.input_validation import WebhookEventPayload
from backend.security.replay import verify_replay
from backend.security.secrets import SecretString, get_secret
from backend.security.tenant import TenantContext, get_current_tenant


def test_hmac_verification():
    secret = "my_super_secret"
    payload = b'{"event":"test"}'
    valid_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_hmac_sha256(secret, payload, valid_sig) is True
    assert verify_hmac_sha256(secret, payload, "invalid_sig") is False

def test_idempotency():
    store = InMemoryIdempotencyStore()
    assert store.register_event("evt_1", "t_1") is True
    assert store.register_event("evt_1", "t_1") is False # Duplicate
    assert store.has_seen("evt_1", "t_1") is True
    assert store.has_seen("evt_2", "t_1") is False

def test_replay_protection():
    # replay_protection calls global store, so we mock it implicitly or just run it
    now = int(time.time())
    assert verify_replay("evt_unique_99", now) is True

    # 6 minutes ago should fail (max is 5)
    assert verify_replay("evt_unique_100", now - 360) is False

def test_tenant_isolation():
    assert get_current_tenant() is None
    with TenantContext("tenant_A"):
        assert get_current_tenant() == "tenant_A"
    assert get_current_tenant() is None

def test_dlp_redaction():
    raw_data = {"card_pan": "4111", "tokens": ["tok_1"]}
    redacted = redact_sensitive_data(raw_data)
    assert redacted["card_pan"] == "[REDACTED]"
