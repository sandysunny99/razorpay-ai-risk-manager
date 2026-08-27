from datetime import timedelta

import pytest

from app.core.auth import Role, create_access_token, decode_access_token


def test_create_and_decode_jwt_token():
    """Valid JWT is created with correct subject and role claims."""
    token = create_access_token(subject="user@razorpay.test", role=Role.ADMIN)
    payload = decode_access_token(token)
    assert payload["sub"] == "user@razorpay.test"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_role_hierarchy_values():
    """Verify Role enum values align with specification."""
    assert Role.VIEWER == "viewer"
    assert Role.OPERATOR == "operator"
    assert Role.ADMIN == "admin"


def test_expired_jwt_token():
    """Expired JWT token raises an error upon decoding."""
    from jose import JWTError
    expired_token = create_access_token(
        subject="user@razorpay.test",
        role=Role.VIEWER,
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(JWTError):
        decode_access_token(expired_token)
