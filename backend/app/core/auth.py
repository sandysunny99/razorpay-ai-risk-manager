# backend/app/core/auth.py
"""
API Authentication & Role-Based Access Control (RBAC) Layer
=============================================================
Supports:
1. Bearer API Secret Key (constant-time hmac.compare_digest)
2. JWT Access Tokens with Role Hierarchy:
   - VIEWER   (read-only SOC queries)
   - OPERATOR (mitigation & demo triggers)
   - ADMIN    (destructive resets & system config)
3. Advisory Bypass in Demo/DRY_RUN mode (never blocks evaluation).
"""
from datetime import datetime, timedelta, timezone
from enum import Enum
import hmac
import logging
from typing import Any, Callable, Dict, Optional

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger("auth")

_bearer_scheme = HTTPBearer(auto_error=False)


class Role(str, Enum):
    VIEWER = "viewer"       # Read-only SOC analyst
    OPERATOR = "operator"   # L1 analyst / demo trigger operator
    ADMIN = "admin"         # L2 supervisor / system admin


_ROLE_HIERARCHY = {
    Role.VIEWER: 1,
    Role.OPERATOR: 2,
    Role.ADMIN: 3,
}


def _keys_match(provided: str, expected: str) -> bool:
    """Constant-time comparison to prevent timing side-channel attacks."""
    return hmac.compare_digest(
        provided.encode("utf-8"),
        expected.encode("utf-8"),
    )


def create_access_token(
    subject: str,
    role: Role = Role.VIEWER,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed HMAC-SHA256 JWT access token with designated role."""
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta is not None else timedelta(hours=24)
    )
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role.value,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    secret = settings.HMAC_SECRET_KEY or "ci_test_hmac_secret_key_only_for_testing_2026"
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and cryptographically validates a JWT token."""
    secret = settings.HMAC_SECRET_KEY or "ci_test_hmac_secret_key_only_for_testing_2026"
    return dict(jwt.decode(token, secret, algorithms=["HS256"]))


def verify_role(required_role: Role) -> Callable[..., Dict[str, Any]]:
    """
    FastAPI dependency factory enforcing minimum RBAC permission level.
    In DEMO / DRY_RUN mode, permits requests with advisory warning if token absent.
    """
    async def _role_dependency(
        credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
    ) -> Dict[str, Any]:
        # Demo / DRY_RUN bypass mode
        if settings.DRY_RUN or settings.APP_MODE == "demo":
            if credentials is None:
                return {"sub": "demo-operator", "role": required_role.value}
            try:
                payload = decode_access_token(credentials.credentials)
                return payload
            except JWTError:
                logger.warning("AUTH_WARN: Invalid JWT provided in demo mode; allowing demo access.")
                return {"sub": "demo-operator", "role": required_role.value}

        # Production enforcement
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = decode_access_token(credentials.credentials)
            user_role_str = payload.get("role", Role.VIEWER.value)
            user_role = Role(user_role_str)
            if _ROLE_HIERARCHY.get(user_role, 0) < _ROLE_HIERARCHY.get(required_role, 0):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: requires {required_role.value} role.",
                )
            return payload
        except (JWTError, ValueError) as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from err

    return _role_dependency


def require_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> None:
    """
    FastAPI dependency — verifies Bearer API key.
    """
    api_key = settings.API_SECRET_KEY

    # Demo / DRY_RUN mode: auth is advisory, never blocking
    if settings.DRY_RUN or settings.APP_MODE == "demo":
        if not api_key:
            return
        if credentials is None:
            return
        if not _keys_match(credentials.credentials, api_key):
            logger.warning("AUTH_WARN: Wrong API key in demo/DRY_RUN mode — request accepted anyway.")
        return

    # Production mode: auth is mandatory
    if not api_key:
        logger.error(
            "SECURITY_CONFIG_ERROR: DRY_RUN=false but API_SECRET_KEY is not set. "
            "Refusing all requests to protect production data."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: authentication not configured.",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not _keys_match(credentials.credentials, api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )
