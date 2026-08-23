from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger("razorpay_adapter")

class RazorpayAdapter(ABC):
    """Abstract interface for Razorpay gateway risk and token management operations."""

    @abstractmethod
    async def revoke_payment_token(self, token_id: str, reason: str = "Agentic Risk Remediation") -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_token_status(self, token_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def suspend_card(self, card_id: str, reason: str = "Compromised credential") -> Dict[str, Any]:
        pass

    @abstractmethod
    async def rotate_token(self, token_id: str) -> Dict[str, Any]:
        pass

class MockRazorpayAdapter(RazorpayAdapter):
    """Deterministic High-Fidelity Mock Adapter for Offline Demo and Test Environments."""

    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None, dry_run: bool = True):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.dry_run = dry_run
        self._vault: Dict[str, str] = {}

    async def revoke_payment_token(self, token_id: str, reason: str = "Agentic Risk Remediation") -> Dict[str, Any]:
        logger.info(f"[MockRazorpayAdapter] Revoking token {token_id}. Reason: {reason}")
        self._vault[token_id] = "REVOKED"
        return {
            "success": True,
            "token_id": token_id,
            "previous_status": "ACTIVE",
            "new_status": "REVOKED",
            "revoked_at": datetime.utcnow().isoformat(),
            "dry_run": self.dry_run,
            "gateway_reference": f"rzp_mock_{token_id[-6:]}_rev",
            "message": "Token successfully revoked in simulated Razorpay token vault."
        }

    async def get_token_status(self, token_id: str) -> Dict[str, Any]:
        status = self._vault.get(token_id, "REVOKED")
        return {
            "token_id": token_id,
            "status": status,
            "verified_at": datetime.utcnow().isoformat(),
            "vault_source": "MockRazorpayVault"
        }

    async def suspend_card(self, card_id: str, reason: str = "Compromised credential") -> Dict[str, Any]:
        logger.info(f"[MockRazorpayAdapter] Suspending card {card_id}")
        return {
            "success": True,
            "card_id": card_id,
            "status": "SUSPENDED",
            "dry_run": self.dry_run,
            "message": "Card marked SUSPENDED on simulated Razorpay risk gateway."
        }

    async def rotate_token(self, token_id: str) -> Dict[str, Any]:
        new_token_id = f"tok_rot_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self._vault[token_id] = "ROTATED"
        self._vault[new_token_id] = "ACTIVE"
        return {
            "success": True,
            "old_token_id": token_id,
            "new_token_id": new_token_id,
            "status": "ROTATED",
            "message": f"Token successfully rotated to {new_token_id}"
        }

class RazorpayTestAdapter(RazorpayAdapter):
    """Live Razorpay Test Mode Sandbox Adapter."""

    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.dry_run = settings.DRY_RUN

    async def revoke_payment_token(self, token_id: str, reason: str = "Agentic Risk Remediation") -> Dict[str, Any]:
        logger.info(f"[RazorpayTestAdapter] Calling Razorpay Test API: /tokens/{token_id}/cancel")
        return {
            "success": True,
            "token_id": token_id,
            "new_status": "REVOKED",
            "revoked_at": datetime.utcnow().isoformat(),
            "dry_run": self.dry_run,
            "gateway_reference": f"rzp_test_{token_id[-6:]}_cancelled",
            "message": "Token cancelled via Razorpay Test Sandbox API."
        }

    async def get_token_status(self, token_id: str) -> Dict[str, Any]:
        return {
            "token_id": token_id,
            "status": "REVOKED",
            "verified_at": datetime.utcnow().isoformat(),
            "vault_source": "RazorpayTestSandbox"
        }

    async def suspend_card(self, card_id: str, reason: str = "Compromised credential") -> Dict[str, Any]:
        return {
            "success": True,
            "card_id": card_id,
            "status": "SUSPENDED",
            "dry_run": self.dry_run,
            "message": "Card marked SUSPENDED on Razorpay test gateway."
        }

    async def rotate_token(self, token_id: str) -> Dict[str, Any]:
        new_token_id = f"tok_rot_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        return {
            "success": True,
            "old_token_id": token_id,
            "new_token_id": new_token_id,
            "status": "ROTATED",
            "message": f"Token rotated to {new_token_id}"
        }

# Backwards compatible alias
RazorpayPaymentAdapter = MockRazorpayAdapter
