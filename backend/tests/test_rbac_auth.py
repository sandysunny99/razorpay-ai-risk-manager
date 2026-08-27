"""
Role-Based Access Control (RBAC) & Authentication Security Tests
================================================================
Tests:
1. JWT token generation with user, role, and merchant claims.
2. Expiration and invalid token cryptographic verification.
3. Role hierarchy enforcement (Viewer < Analyst/Operator < Admin).
4. Login API endpoint: valid credentials, invalid password, deactivated accounts.
5. Profile (/me) and logout endpoints.
6. Admin-only mutation protection.
"""
from datetime import timedelta

from fastapi import HTTPException
from fastapi.testclient import TestClient
from jose import JWTError
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import (
    Role,
    create_access_token,
    decode_access_token,
    verify_role,
)
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.entities import User


@pytest.fixture
def auth_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    # Seed test users
    u_admin = User(
        user_id="usr_admin",
        username="test_admin",
        email="admin@test.com",
        hashed_password=hash_password("AdminPass@2026!"),
        role="admin",
        merchant_id="default",
        is_active=True
    )
    u_analyst = User(
        user_id="usr_analyst",
        username="test_analyst",
        email="analyst@test.com",
        hashed_password=hash_password("AnalystPass@2026!"),
        role="analyst",
        merchant_id="default",
        is_active=True
    )
    u_viewer = User(
        user_id="usr_viewer",
        username="test_viewer",
        email="viewer@test.com",
        hashed_password=hash_password("ViewerPass@2026!"),
        role="viewer",
        merchant_id="default",
        is_active=True
    )
    u_inactive = User(
        user_id="usr_inactive",
        username="test_disabled",
        email="disabled@test.com",
        hashed_password=hash_password("DisabledPass@2026!"),
        role="viewer",
        merchant_id="default",
        is_active=False
    )
    db.add_all([u_admin, u_analyst, u_viewer, u_inactive])
    db.commit()

    yield db
    db.close()


@pytest.fixture
def auth_client(auth_test_db):
    def override_get_db():
        try:
            yield auth_test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_db, None)


def test_create_and_decode_jwt_token_with_tenant():
    """Valid JWT is created with correct subject, role, and merchant claims."""
    token = create_access_token(
        subject="analyst_1",
        role=Role.ANALYST,
        merchant_id="merchant_demo_01",
        email="analyst@demo.com"
    )
    payload = decode_access_token(token)
    assert payload["sub"] == "analyst_1"
    assert payload["username"] == "analyst_1"
    assert payload["role"] == "analyst"
    assert payload["merchant_id"] == "merchant_demo_01"
    assert payload["email"] == "analyst@demo.com"
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_role_hierarchy_values():
    """Verify Role enum values align with specification."""
    assert Role.VIEWER == "viewer"
    assert Role.ANALYST == "analyst"
    assert Role.OPERATOR == "operator"
    assert Role.ADMIN == "admin"


def test_expired_jwt_token():
    """Expired JWT token raises an error upon decoding."""
    expired_token = create_access_token(
        subject="user@razorpay.test",
        role=Role.VIEWER,
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(JWTError):
        decode_access_token(expired_token)


def test_invalid_signature_jwt_rejected():
    """Token signed with wrong key is rejected."""
    from jose import jwt
    fake_token = jwt.encode({"sub": "attacker", "role": "admin"}, "wrong_key_secret_2026", algorithm="HS256")
    with pytest.raises(JWTError):
        decode_access_token(fake_token)


@pytest.mark.asyncio
async def test_rbac_hierarchy_enforcement():
    """Verify verify_role dependency allows higher role and rejects lower role."""
    from fastapi.security import HTTPAuthorizationCredentials

    admin_token = create_access_token(subject="admin", role=Role.ADMIN)
    viewer_token = create_access_token(subject="viewer", role=Role.VIEWER)

    admin_check = verify_role(Role.ADMIN)
    # Admin calling admin-only endpoint: ALLOWED
    res = await admin_check(HTTPAuthorizationCredentials(scheme="Bearer", credentials=admin_token))
    assert res["role"] == "admin"

    # Viewer calling admin-only endpoint: FORBIDDEN 403
    with pytest.raises(HTTPException) as exc_info:
        await admin_check(HTTPAuthorizationCredentials(scheme="Bearer", credentials=viewer_token))
    assert exc_info.value.status_code == 403
    assert "Insufficient permissions" in exc_info.value.detail


def test_auth_login_successful(auth_client):
    """POST /api/v1/auth/login succeeds with valid credentials."""
    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "test_admin", "password": "AdminPass@2026!"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"
    assert data["username"] == "test_admin"
    assert data["merchant_id"] == "default"


def test_auth_login_invalid_password(auth_client):
    """POST /api/v1/auth/login rejects incorrect password with 401."""
    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "test_admin", "password": "WrongPassword!"}
    )
    assert resp.status_code == 401
    assert "Invalid username or password" in resp.json()["detail"]


def test_auth_login_deactivated_account(auth_client):
    """POST /api/v1/auth/login rejects deactivated user with 403."""
    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "test_disabled", "password": "DisabledPass@2026!"}
    )
    assert resp.status_code == 403
    assert "Account is deactivated" in resp.json()["detail"]


def test_auth_me_endpoint(auth_client):
    """GET /api/v1/auth/me returns authenticated user profile."""
    # First login to obtain token
    login_resp = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "test_analyst", "password": "AnalystPass@2026!"}
    )
    token = login_resp.json()["access_token"]

    # Request profile
    me_resp = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["username"] == "test_analyst"
    assert data["role"] == "analyst"
    assert data["merchant_id"] == "default"
    assert data["is_active"] is True


def test_auth_logout_endpoint(auth_client):
    """POST /api/v1/auth/logout confirms session logout."""
    valid_token = create_access_token("test_analyst", role=Role.ANALYST)
    resp = auth_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "LOGGED_OUT"
