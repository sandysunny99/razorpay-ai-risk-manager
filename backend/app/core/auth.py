# backend/app/core/auth.py
"""
Phase 3 — API Authentication Layer
===================================
Option A: API key in `Authorization: Bearer <key>` header, verified with
hmac.compare_digest. Chosen because:
1. Demo-friendly — frontend just sets a VITE_API_KEY env var; no user DB needed.
2. Render-compatible — the API key lives in a Render secret env var.
3. DRY_RUN bypass — in demo/DRY_RUN mode, auth is optional (warns, never blocks).
"""
import hmac
import logging
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

logger = logging.getLogger("auth")

_bearer_scheme = HTTPBearer(auto_error=False)


def _keys_match(provided: str, expected: str) -> bool:
    """Constant-time comparison to prevent timing side-channel attacks."""
    return hmac.compare_digest(
        provided.encode("utf-8"),
        expected.encode("utf-8"),
    )


def require_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> None:
    """
    FastAPI dependency — verifies Bearer API key.

    Behaviour matrix:
    | DRY_RUN | API_SECRET_KEY set | Credential provided | Outcome            |
    |---------|-------------------|---------------------|-------------------|
    | True    | No                | Any                 | WARN + PASS        |
    | True    | Yes               | Wrong               | WARN + PASS        |
    | False   | No                | Any                 | 500 CONFIG ERROR   |
    | False   | Yes               | Wrong / Missing     | 401                |
    | False   | Yes               | Correct             | 200 PASS           |
    """
    api_key = settings.API_SECRET_KEY

    # Demo / DRY_RUN mode: auth is advisory, never blocking
    if settings.DRY_RUN or settings.APP_MODE == "demo":
        if not api_key:
            logger.warning(
                "AUTH_BYPASS: API_SECRET_KEY not configured. "
                "Running in demo/DRY_RUN mode — all requests accepted."
            )
            return
        if credentials is None:
            logger.warning(
                "AUTH_BYPASS: No Authorization header in demo/DRY_RUN mode — request accepted."
            )
            return
        if not _keys_match(credentials.credentials, api_key):
            logger.warning(
                "AUTH_WARN: Wrong API key in demo/DRY_RUN mode — request accepted anyway."
            )
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
