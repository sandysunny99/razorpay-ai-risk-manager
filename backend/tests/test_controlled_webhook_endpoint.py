import hashlib
import hmac
import json
import uuid

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.main import app
from app.models.entities import Merchant, MerchantWebhookRegistration, WebhookEvent


@pytest.fixture
def client():
    return TestClient(app)

def _create_merchant_and_registration(db, merchant_id: str, endpoint_id: str, secret: str):
    merchant = Merchant(merchant_id=merchant_id, name="Test Merchant")
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    registration = MerchantWebhookRegistration(
        endpoint_id=endpoint_id,
        merchant_id=merchant.id,
        secret=secret,
        active=True,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return merchant, registration

def _sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

def test_valid_hmac_and_processing(monkeypatch, client):
    # Generate deterministic values
    merchant_id = f"m{uuid.uuid4().hex[:8]}"
    endpoint_id = f"ep{uuid.uuid4().hex[:8]}"
    secret = "secret123"

    def override_get_db():
        db = SessionLocal()
        # Cleanup previous data to ensure isolation
        db.query(MerchantWebhookRegistration).delete()
        db.query(Merchant).delete()
        db.query(WebhookEvent).delete()
        db.commit()
        _create_merchant_and_registration(db, merchant_id, endpoint_id, secret)
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    payload = {"event": "payment.authorized", "payload": {"amount": 1000}}
    raw_body = json.dumps(payload).encode("utf-8")
    sig = _sign(raw_body, secret)
    response = client.post(
        f"/api/v1/webhooks/razorpay/{endpoint_id}",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig, "X-Razorpay-Event-Id": "evt1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INGESTED"
    assert data["processed"] is True
    # Verify DB persistence
    db = SessionLocal()
    ev = db.query(WebhookEvent).filter(WebhookEvent.event_id == "evt1").first()
    assert ev is not None
    # Convert stored merchant_id to int for comparison
    assert int(ev.merchant_id) == db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first().id
    db.close()

def test_invalid_signature(monkeypatch, client):
    # Generate deterministic values
    merchant_id = f"m{uuid.uuid4().hex[:8]}"
    endpoint_id = f"ep{uuid.uuid4().hex[:8]}"
    secret = "secret456"
    def override_get_db():
        db = SessionLocal()
        # Clean previous test data
        db.query(MerchantWebhookRegistration).delete()
        db.query(Merchant).delete()
        db.commit()
        _create_merchant_and_registration(db, merchant_id, endpoint_id, secret)
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    # Create fresh client after override (no middleware needed)
    client = TestClient(app)

    payload = {"event": "payment.authorized", "payload": {}}
    raw_body = json.dumps(payload).encode("utf-8")
    # Intentionally bad signature
    response = client.post(
        f"/api/v1/webhooks/razorpay/{endpoint_id}",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": "bad_sig"},
    )
    assert response.status_code == 401

def test_unknown_endpoint(monkeypatch, client):
    def override_get_db():
        db = SessionLocal()
        # No registration created
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    payload = {"event": "payment.authorized", "payload": {}}
    raw_body = json.dumps(payload).encode("utf-8")
    sig = _sign(raw_body, "anysecret")
    response = client.post(
        "/api/v1/webhooks/razorpay/notexist",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert response.status_code == 404

def test_duplicate_event_id(monkeypatch, client):
    endpoint_id = f"ep{uuid.uuid4().hex[:8]}"
    def override_get_db():
        db = SessionLocal()
        # Clean previous test data
        db.query(MerchantWebhookRegistration).delete()
        db.query(Merchant).delete()
        db.commit()
        merchant_id = f"m{uuid.uuid4().hex[:8]}"
        _create_merchant_and_registration(db, merchant_id, endpoint_id, "secret321")
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    payload = {"event": "payment.authorized", "payload": {}}
    raw_body = json.dumps(payload).encode("utf-8")
    sig = _sign(raw_body, "secret321")
    headers = {"Content-Type": "application/json", "X-Razorpay-Signature": sig, "X-Razorpay-Event-Id": "dup_evt"}
    # First call – should ingest
    resp1 = client.post(
        f"/api/v1/webhooks/razorpay/{endpoint_id}",
        content=raw_body,
        headers=headers,
    )
    assert resp1.status_code == 200
    # Second call – within duplicate window, should be ignored
    resp2 = client.post(
        f"/api/v1/webhooks/razorpay/{endpoint_id}",
        content=raw_body,
        headers=headers,
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "DUPLICATE_IGNORED"

def test_replay_with_new_event_id(monkeypatch, client):
    # Unique merchant for this test
    endpoint_id = f"ep{uuid.uuid4().hex[:8]}"
    merchant_id = f"m{uuid.uuid4().hex[:8]}"

    # Create merchant and registration once before any request
    db_setup = SessionLocal()
    # Ensure isolation by cleaning tables
    db_setup.query(MerchantWebhookRegistration).delete()
    db_setup.query(Merchant).delete()
    db_setup.query(WebhookEvent).delete()
    db_setup.commit()
    _create_merchant_and_registration(db_setup, merchant_id, endpoint_id, "secret654")
    db_setup.close()

    # Dependency that provides a fresh DB session per request
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    payload = {"event": "payment.authorized", "payload": {"amount": 2000}}
    raw_body = json.dumps(payload).encode("utf-8")
    sig = _sign(raw_body, "secret654")

    # First event id
    resp1 = client.post(
        f"/api/v1/webhooks/razorpay/{endpoint_id}",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig, "X-Razorpay-Event-Id": "eid1"},
    )
    assert resp1.status_code == 200
    # Replay with different event id (new) – should be ingested as a new event
    resp2 = client.post(
        f"/api/v1/webhooks/razorpay/{endpoint_id}",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig, "X-Razorpay-Event-Id": "eid2"},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "INGESTED"
    # Verify two distinct DB rows
    db = SessionLocal()
    evs = db.query(WebhookEvent).all()
    assert len(evs) == 2
    db.close()
