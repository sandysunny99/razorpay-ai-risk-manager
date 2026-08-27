from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from app.models.entities import PaymentToken, Card

class TokenRiskEngine:
    """
    Token Risk Engine & Zombie Token Detector.
    
    ZOMBIE TOKEN DEFINITION:
    A payment token remains ACTIVE on merchant/vault records despite the 
    underlying credit card being EXPIRED, BLOCKED, or SUSPENDED. If this 
    token is actively used for authorization, it represents severe risk of 
    unauthorized recurring billing, token hijacking, or failure to remediate.
    """

    def evaluate(self, token: Optional[PaymentToken], card: Card) -> Dict[str, Any]:
        if not token:
            return {
                "score": 0.0,
                "reasons": ["No payment token utilized for transaction"],
                "is_zombie": False,
                "zombie_reason": None,
                "token_status": "NONE"
            }

        score = 0.0
        reasons: List[str] = []
        is_zombie = False
        zombie_reason: Optional[str] = None
        now = datetime.now(timezone.utc)

        # Check if underlying card is expired or inactive
        card_is_dead = card.is_expired or card.status in ["EXPIRED", "BLOCKED", "SUSPENDED"]

        # Zombie Token Condition
        if token.status == "ACTIVE" and card_is_dead:
            is_zombie = True
            zombie_reason = f"CRITICAL ZOMBIE TOKEN: Token {token.token_id} is ACTIVE while parent card {card.masked_pan} status is {card.status} (Expired: {card.is_expired})"
            score += 85.0
            reasons.append(zombie_reason)
        elif token.status == "REVOKED":
            score += 0.0
            reasons.append(f"Token {token.token_id} is properly REVOKED (Zero active liability)")
        elif token.status == "ACTIVE":
            # Active token attached to active card
            score += 15.0  # Base active token factor (provides surface if exposed)
            reasons.append(f"Active token {token.token_id} (Age: {token.token_age_days}d, Usages: {token.usage_count})")

        # Age/Velocity Check on Token
        if token.usage_count > 50 and token.token_age_days < 2:
            score += 20.0
            reasons.append(f"Abnormal token usage spike: {token.usage_count} authorizations in {token.token_age_days} days")

        normalized_score = min(100.0, score)
        return {
            "score": normalized_score,
            "reasons": reasons,
            "is_zombie": is_zombie,
            "zombie_reason": zombie_reason,
            "token_status": token.status,
            "token_id": token.token_id
        }

    def detect_zombie_tokens(self, tokens_with_cards: List[tuple[PaymentToken, Card]]) -> List[Dict[str, Any]]:
        """Batch scanner to detect all zombie tokens in the portfolio."""
        zombies = []
        for token, card in tokens_with_cards:
            result = self.evaluate(token, card)
            if result["is_zombie"]:
                zombies.append({
                    "token_id": token.token_id,
                    "card_id": card.card_id,
                    "masked_pan": card.masked_pan,
                    "card_status": card.status,
                    "is_card_expired": card.is_expired,
                    "token_status": token.status,
                    "last_used": token.last_used_at.isoformat() if token.last_used_at else "Never",
                    "risk_level": "CRITICAL" if result["score"] >= 75 else "HIGH",
                    "reason": result["zombie_reason"]
                })
        return zombies
