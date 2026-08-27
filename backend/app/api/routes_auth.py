"""
Authentication & Role-Based Access Control (RBAC) API Router
=============================================================
Provides:
- POST /api/v1/auth/login: Authenticate user, issue short-lived JWT with tenant claims.
- GET  /api/v1/auth/me: Retrieve current authenticated user profile and permissions.
- POST /api/v1/auth/logout: Client session acknowledgment and audit trail logging.
"""
import logging
from typing import Any, Dict
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import Role, create_access_token, get_current_user
from app.core.database import get_db
from app.core.security import verify_password
from app.engines.audit_ledger import AuditLedgerEngine
from app.models.entities import User

logger = logging.getLogger("auth_api")
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & RBAC"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds
    role: str
    merchant_id: str
    username: str


class UserProfileResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    merchant_id: str
    is_active: bool


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticate SOC user credentials and issue signed JWT access token.
    Enforces password verification, account active checks, and audit logging.
    """
    user = db.query(User).filter(User.username == request.username).first()

    if not user or not verify_password(request.password, user.hashed_password):
        # Record security audit event for failed login attempt
        try:
            AuditLedgerEngine.append_event(
                db=db,
                event_id=f"AUTH-FAIL-{uuid.uuid4().hex[:8].upper()}",
                actor=request.username,
                decision="LOGIN_FAILED",
                risk_score=60.0,
                policy="AUTH_POLICY_ZERO_TRUST",
                tool="auth.login",
                action_requested="AUTHENTICATE",
                action_executed="DENIED",
                verification="FAILED",
                details={"reason": "Invalid credentials", "attempted_user": request.username},
                merchant_id="default"
            )
        except Exception as audit_err:
            logger.warning("Failed to record login failure audit event: %s", audit_err)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact security administrator.",
        )

    # Issue short-lived 30-minute access token with tenant claim
    role_enum = Role(user.role) if user.role in [r.value for r in Role] else Role.VIEWER
    token = create_access_token(
        subject=user.username,
        role=role_enum,
        merchant_id=user.merchant_id,
        email=user.email,
    )

    # Record security audit event for successful authentication
    try:
        AuditLedgerEngine.append_event(
            db=db,
            event_id=f"AUTH-OK-{uuid.uuid4().hex[:8].upper()}",
            actor=user.username,
            decision="LOGIN_SUCCESS",
            risk_score=0.0,
            policy="AUTH_POLICY_ZERO_TRUST",
            tool="auth.login",
            action_requested="AUTHENTICATE",
            action_executed="PERMITTED",
            verification="VERIFIED",
            details={
                "role": user.role,
                "merchant_id": user.merchant_id,
                "user_id": user.user_id
            },
            merchant_id=user.merchant_id
        )
    except Exception as audit_err:
        logger.warning("Failed to record login success audit event: %s", audit_err)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=1800,
        role=user.role,
        merchant_id=user.merchant_id,
        username=user.username,
    )


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    claims: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserProfileResponse:
    """
    Returns the authenticated user's profile and active merchant context.
    """
    username = claims.get("username") or claims.get("sub", "unknown")
    user = db.query(User).filter(User.username == username).first()

    if user:
        return UserProfileResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            role=user.role,
            merchant_id=user.merchant_id,
            is_active=user.is_active,
        )

    # Demo fallback profile if user not seeded in DB
    return UserProfileResponse(
        user_id="usr_demo_01",
        username=username,
        email=claims.get("email", "demo@internal.razorpay"),
        role=claims.get("role", Role.VIEWER.value),
        merchant_id=claims.get("merchant_id", "default"),
        is_active=True,
    )


@router.post("/logout")
def logout(claims: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, str]:
    """
    Logs out the current session and emits confirmation.
    """
    username = claims.get("username") or claims.get("sub", "unknown")
    logger.info("User logged out: %s", username)
    return {"status": "LOGGED_OUT", "message": f"User {username} successfully logged out."}
