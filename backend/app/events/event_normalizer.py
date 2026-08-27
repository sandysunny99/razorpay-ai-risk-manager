import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.events.event_model import SecurityEvent, EventType
from app.core.security import generate_card_fingerprint

class EventNormalizer:
    """
    Normalizes heterogeneous external vendor payloads (Razorpay, Cloudflare, CTI)
    into standard internal SecurityEvent objects with PCI-safe field sanitization.
    """

    @classmethod
    def normalize_razorpay_webhook(cls, payload: Dict[str, Any], event_name: str) -> SecurityEvent:
        event_mapping = {
            "payment.authorized": EventType.PAYMENT_AUTHORIZED,
            "payment.captured": EventType.PAYMENT_CAPTURED,
            "payment.failed": EventType.PAYMENT_FAILED,
            "order.paid": EventType.PAYMENT_CAPTURED,
            "refund.created": EventType.PAYMENT_REFUNDED,
        }
        event_type = event_mapping.get(event_name, EventType.PAYMENT_CREATED)
        
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        if not entity:
            entity = payload.get("payload", {}).get("order", {}).get("entity", {})

        txn_id = entity.get("id", f"pay_test_{uuid.uuid4().hex[:10]}")
        merchant_id = payload.get("account_id") or entity.get("merchant_id", "acc_default_rzp")
        token_id = entity.get("token_id")
        
        # Safe card metadata (No raw PAN)
        card_details = entity.get("card", {})
        card_fingerprint = None
        if isinstance(card_details, dict) and card_details.get("last4"):
            last4 = card_details.get("last4")
            card_fingerprint = generate_card_fingerprint(f"000000000000{last4}")

        return SecurityEvent(
            event_id=f"EVT-RZP-{uuid.uuid4().hex[:8].upper()}",
            event_type=event_type,
            source="RAZORPAY_TEST_MODE",
            timestamp=datetime.now(timezone.utc).isoformat(),
            merchant_id=merchant_id,
            customer_id=entity.get("contact") or entity.get("email"),
            card_fingerprint=card_fingerprint,
            token_id=token_id,
            transaction_id=txn_id,
            request_id=payload.get("event_id"),
            correlation_id=txn_id,
            metadata={
                "amount": entity.get("amount", 0) / 100.0 if entity.get("amount") else 0.0,
                "currency": entity.get("currency", "INR"),
                "status": entity.get("status", "unknown"),
                "method": entity.get("method", "card"),
                "error_code": entity.get("error_code"),
                "error_description": entity.get("error_description"),
                "razorpay_event": event_name,
            }
        )

    @classmethod
    def normalize_cloudflare_signal(cls, headers: Dict[str, str], client_ip: str) -> SecurityEvent:
        cf_ray = headers.get("cf-ray") or f"ray-{uuid.uuid4().hex[:12]}"
        bot_score = 99
        if "cf-bot-score" in headers:
            try:
                bot_score = int(headers["cf-bot-score"])
            except ValueError:
                bot_score = 99

        return SecurityEvent(
            event_id=f"EVT-CF-{uuid.uuid4().hex[:8].upper()}",
            event_type=EventType.CLOUDFLARE_SECURITY_EVENT,
            source="CLOUDFLARE_EDGE",
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=cf_ray,
            correlation_id=cf_ray,
            metadata={
                "cf_ray": cf_ray,
                "bot_score": bot_score,
                "client_ip": client_ip,
                "country": headers.get("cf-ipcountry", "UNKNOWN"),
                "is_bot": bot_score < 30,
            }
        )
