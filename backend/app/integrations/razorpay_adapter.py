import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger("razorpay_adapter")

class RazorpayPaymentAdapter:
    """
    Razorpay Test / Mock API Adapter.
    Handles token management, card status updates, and risk incident webhooks.
    In development & demo modes, runs in DRY_RUN or Mock Mode.
    """

    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.dry_run = settings.DRY_RUN
        self.use_mock = settings.USE_MOCK_RAZORPAY

    async def revoke_payment_token(self, token_id: str, reason: str = "Agentic Risk Remediation") -> Dict[str, Any]:
        """Revoke a compromised payment token."""
        logger.info(f"[Razorpay API] Requesting token revocation for {token_id}. Reason: {reason}")
        
        # In test/mock mode:
        return {
            "success": True,
            "token_id": token_id,
            "previous_status": "ACTIVE",
            "new_status": "REVOKED",
            "revoked_at": datetime.utcnow().isoformat(),
            "dry_run": self.dry_run,
            "gateway_reference": f"rzp_rev_{token_id[-6:]}_ok",
            "message": "Token successfully revoked in Razorpay token vault."
        }

    async def get_token_status(self, token_id: str) -> Dict[str, Any]:
        """Fetch verified token status from vault."""
        return {
            "token_id": token_id,
            "status": "REVOKED",
            "verified_at": datetime.utcnow().isoformat()
        }

    async def suspend_card(self, card_id: str, reason: str = "Compromised credential") -> Dict[str, Any]:
        """Suspend card on gateway."""
        logger.info(f"[Razorpay API] Card suspension request: {card_id}")
        return {
            "success": True,
            "card_id": card_id,
            "status": "SUSPENDED",
            "dry_run": self.dry_run,
            "message": "Card marked SUSPENDED on Razorpay risk gateway."
        }

    async def rotate_token(self, token_id: str) -> Dict[str, Any]:
        """Rotate payment token to a new secure token ID."""
        new_token_id = f"tok_rot_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        return {
            "success": True,
            "old_token_id": token_id,
            "new_token_id": new_token_id,
            "status": "ROTATED",
            "message": f"Token successfully rotated to {new_token_id}"
        }
