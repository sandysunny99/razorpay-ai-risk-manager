from typing import Any, Dict, List

from app.models.entities import PaymentToken, Transaction


class ImpactAnalyzer:
    """
    Computes merchant and customer impact metrics before taking remediation actions.
    Distinguishes legitimate recurring subscriptions from high-risk one-off payments
    to prevent merchant revenue churn and unnecessary customer friction.
    """

    @classmethod
    def analyze_merchant_impact(cls, tokens: List[PaymentToken], recent_txns: List[Transaction]) -> Dict[str, Any]:
        unique_merchants = set(t.merchant_id for t in tokens if t.merchant_id)
        recurring_count = sum(1 for t in tokens if getattr(t, "is_recurring", False) or "sub" in (t.token_id or "").lower())
        total_recent_volume = sum(t.amount for t in recent_txns) if recent_txns else 0.0

        return {
            "affected_merchant_count": len(unique_merchants),
            "affected_merchants": list(unique_merchants),
            "dependent_token_count": len(tokens),
            "recurring_subscription_count": recurring_count,
            "recent_transaction_volume": total_recent_volume,
            "disruption_risk": "HIGH" if recurring_count > 1 else ("MEDIUM" if recurring_count == 1 else "LOW")
        }

    @classmethod
    def analyze_customer_impact(cls, card_id: str, tokens: List[PaymentToken], customer_id: str = "cust_default") -> Dict[str, Any]:
        return {
            "customer_id": customer_id,
            "active_subscriptions": sum(1 for t in tokens if getattr(t, "is_recurring", False)),
            "payment_friction_level": "LOW" if len(tokens) <= 1 else "MODERATE",
            "recommended_notification": "Send card renewal push notice"
        }

impact_analyzer = ImpactAnalyzer()
