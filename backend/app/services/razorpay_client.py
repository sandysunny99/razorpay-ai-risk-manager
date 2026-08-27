"""
backend/app/services/razorpay_client.py
=======================================
Razorpay test API client for demo webhook generation.
Only active when real RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are configured.
Falls back silently when unconfigured — demo uses deterministic synthetic data.
"""
import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class RazorpayTestClient:
    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ) -> None:
        self._key_id = key_id if key_id is not None else settings.RAZORPAY_KEY_ID
        self._key_secret = key_secret if key_secret is not None else settings.RAZORPAY_KEY_SECRET
        self._webhook_secret = webhook_secret if webhook_secret is not None else settings.RAZORPAY_WEBHOOK_SECRET
        self._client: Any = None
        self._available: bool = False
        self._init_client()

    def _init_client(self) -> None:
        if (
            not self._key_id
            or not self._key_secret
            or self._key_id.startswith("rzp_test_mock")
        ):
            logger.info("Razorpay: Unconfigured / mock credentials — using synthetic demo fixtures")
            self._available = False
            return
        try:
            import razorpay
            self._client = razorpay.Client(auth=(self._key_id, self._key_secret))
            self._available = True
            mode = "TEST" if self._key_id.startswith("rzp_test_") else "LIVE"
            logger.info("Razorpay: %s mode client initialized successfully", mode)
        except ImportError:
            logger.warning("Razorpay SDK not installed — falling back to synthetic fixtures")
            self._available = False
        except Exception as e:
            logger.warning("Razorpay client initialization failed: %s", e)
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def create_test_order(self, amount_paise: int, currency: str = "INR") -> Optional[Dict[str, Any]]:
        """Create a test order via Razorpay API. Returns None if unavailable."""
        if not self._available or self._client is None:
            return None
        try:
            order = self._client.order.create({
                "amount": amount_paise,
                "currency": currency,
                "receipt": f"test_receipt_{int(time.time())}",
                "notes": {"demo": "true", "source": "razorpay-ai-risk-manager"},
            })
            logger.info("Razorpay test order created: %s", order.get("id"))
            return dict(order)
        except Exception as e:
            logger.warning("Razorpay create_order failed: %s", e)
            return None

    def generate_test_webhook_payload(
        self,
        event_type: str,
        amount_paise: int = 50000,
        card_network: str = "Visa",
        card_last4: str = "1111",
        payment_id: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Generate a realistic webhook payload with valid HMAC signature.
        Returns: (payload_dict, x-razorpay-signature)
        """
        pid = payment_id or f"pay_{int(time.time())}"
        payload: Dict[str, Any] = {
            "entity": "event",
            "account_id": "acc_TEST12345",
            "event": event_type,
            "contains": ["payment"],
            "payload": {
                "payment": {
                    "entity": {
                        "id": pid,
                        "amount": amount_paise,
                        "currency": "INR",
                        "status": "captured" if "captured" in event_type else "failed",
                        "method": "card",
                        "card": {
                            "id": f"card_TEST{int(time.time())}",
                            "network": card_network,
                            "last4": card_last4,
                            "issuer": "HDFC",
                            "international": False,
                        },
                        "created_at": int(time.time()),
                    }
                }
            },
        }
        payload_str = json.dumps(payload, separators=(",", ":"))
        secret = self._webhook_secret or self._key_secret or "rzp_test_mock_agent_secret"
        signature = hmac.new(
            secret.encode("utf-8"), payload_str.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return payload, signature

    def fetch_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Fetch payment details. Returns None if unavailable."""
        if not self._available or self._client is None:
            return None
        try:
            payment = self._client.payment.fetch(payment_id)
            return dict(payment)
        except Exception as e:
            logger.warning("Razorpay fetch_payment failed: %s", e)
            return None


_default_client: Optional[RazorpayTestClient] = None


def get_razorpay_client() -> RazorpayTestClient:
    """Singleton getter for RazorpayTestClient."""
    global _default_client
    if _default_client is None:
        _default_client = RazorpayTestClient()
    return _default_client
