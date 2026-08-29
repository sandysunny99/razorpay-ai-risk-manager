import uuid

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.core.auth import Role, create_access_token, verify_role
from app.core.database import SessionLocal, get_db
from app.main import app
from app.models.entities import Merchant, MerchantWebhookRegistration


@pytest.fixture
def client():
    return TestClient(app)

def _create_merchant(db: Session, merchant_id: str):
    merchant = Merchant(merchant_id=merchant_id, name="Test Merchant")
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant

def test_admin_can_create_registration(client):
    merchant_id = f"m{uuid.uuid4().hex[:8]}"
    # Override DB dependency to use a fresh session
    def override_get_db():
        db = SessionLocal()
        try:
            _create_merchant(db, merchant_id)
        except Exception:
            db.rollback()
        try:
            # Ensure registration exists for admin test; handled in request
            pass
        finally:
            yield db
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    response = client.post(f"/admin/merchants/{merchant_id}/webhook-registrations")
    assert response.status_code == 200
    data = response.json()
    # secret must not be in response
    assert "secret" not in data
    # endpoint_id should be present and non‑empty
    assert data.get("endpoint_id")
    # Verify DB entry matches
    db = SessionLocal()
    reg = db.query(MerchantWebhookRegistration).filter(MerchantWebhookRegistration.endpoint_id == data["endpoint_id"]).first()
    assert reg is not None
    merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
    assert reg.merchant_id == merchant.id
    db.close()

def test_non_admin_is_denied(monkeypatch, client):
    merchant_id = "m123"
    # Create merchant and registration in DB
    def override_get_db():
        db = SessionLocal()
        # Clean previous data to ensure isolation
        db.query(MerchantWebhookRegistration).delete()
        db.query(Merchant).delete()
        db.commit()
        # Ensure merchant exists (idempotent)
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            merchant = Merchant(merchant_id=merchant_id, name="Test Merchant")
            db.add(merchant)
            db.commit()
            db.refresh(merchant)
        # Ensure registration exists
        registration = db.query(MerchantWebhookRegistration).filter(MerchantWebhookRegistration.endpoint_id == "ep_nonadmin").first()
        if not registration:
            registration = MerchantWebhookRegistration(
                endpoint_id="ep_nonadmin",
                merchant_id=merchant.id,
                secret="secret_nonadmin",
                active=True,
            )
            db.add(registration)
            db.commit()
            db.refresh(registration)
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    # Override role dependency to simulate non‑admin user
    # Instead of overriding the dependency (which requires the exact callable), we provide an auth token with VIEWER role.
    token = create_access_token("test_user", role=Role.VIEWER)
    headers = {"Authorization": f"Bearer {token}"}
    # Create fresh client after overrides
    client = TestClient(app)
    # Simulate request without admin role – should be 401/403
    response = client.post(
        "/admin/merchants/m123/webhook-registrations",
        headers=headers,
    )
    assert response.status_code in (401, 403)



def test_invalid_merchant_returns_404(client):
    # Override DB dependency to use a fresh session
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    response = client.post("/admin/merchants/notexist/webhook-registrations")
    assert response.status_code == 404
