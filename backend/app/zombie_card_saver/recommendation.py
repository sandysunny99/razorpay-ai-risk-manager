from typing import Dict, Any, List
from app.models.entities import PaymentToken
from app.zombie_card_saver.schemas import ZombieActionType, ZombieSeverity

class ZombieRecommendationEngine:
    """
    Generates intelligent remediation recommendations:
    - Highly exposed/critical tokens -> REVOKE_TOKEN
    - High-velocity/suspicious tokens -> REQUEST_STEP_UP / REVIEW
    - Recurring subscription merchant tokens -> REVIEW / RELINK_TOKEN (to prevent billing failure)
    - Stale dormant tokens on expired cards -> MONITOR / DEFER
    """

    @classmethod
    def recommend_for_card(cls, severity: ZombieSeverity, risk_score: float, has_recurring: bool) -> ZombieActionType:
        if risk_score >= 75.0 or severity == ZombieSeverity.CRITICAL:
            return ZombieActionType.REVOKE_TOKEN
        if has_recurring:
            return ZombieActionType.REVIEW
        if risk_score >= 40.0 or severity == ZombieSeverity.HIGH:
            return ZombieActionType.REQUEST_STEP_UP
        if severity == ZombieSeverity.MEDIUM:
            return ZombieActionType.REVIEW
        return ZombieActionType.MONITOR

    @classmethod
    def recommend_for_token(cls, token: PaymentToken, card_risk: float, is_recurring: bool, token_risk: float) -> ZombieActionType:
        composite = max(card_risk, token_risk)
        if composite >= 75.0:
            return ZombieActionType.REVOKE_TOKEN
        if is_recurring:
            return ZombieActionType.REVIEW
        if composite >= 40.0:
            return ZombieActionType.REQUEST_STEP_UP
        return ZombieActionType.MONITOR

zombie_recommender = ZombieRecommendationEngine()
