from datetime import datetime, timezone
from typing import Any, Dict, List

from app.models.entities import Card


class CardRiskEngine:
    """
    Card Risk Engine.
    Evaluates:
    - Card status (ACTIVE vs EXPIRED vs SUSPENDED vs BLOCKED)
    - Expiration state
    - Failed authorization attempt velocity
    - Historical fraud / chargeback record on the card
    """

    def evaluate(self, card: Card) -> Dict[str, Any]:
        score = 0.0
        reasons: List[str] = []
        now = datetime.now(timezone.utc)

        # 1. Expiration Check
        if card.is_expired or card.expiry_year < now.year or (card.expiry_year == now.year and card.expiry_month < now.month):
            score += 40.0
            reasons.append(f"Card is mathematically expired (Exp: {card.expiry_month:02d}/{card.expiry_year})")

        # 2. Card Status Check
        if card.status == "BLOCKED":
            score += 50.0
            reasons.append("Card is already in BLOCKED status")
        elif card.status == "SUSPENDED":
            score += 30.0
            reasons.append("Card is currently SUSPENDED pending review")

        # 3. Failed Attempts
        if card.failed_attempts >= 3:
            score += 25.0
            reasons.append(f"Multiple recent failed authorization attempts: {card.failed_attempts}")
        elif card.failed_attempts > 0:
            score += 10.0
            reasons.append(f"Recent failed authorization attempt: {card.failed_attempts}")

        # 4. Previous Fraud History
        if card.previous_fraud_count > 0:
            score += 25.0
            reasons.append(f"Previous fraud incidents linked to card: {card.previous_fraud_count}")

        normalized_score = min(100.0, score)
        return {
            "score": normalized_score,
            "reasons": reasons,
            "card_status": card.status,
            "is_expired": card.is_expired
        }
