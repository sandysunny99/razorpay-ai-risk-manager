from datetime import datetime, timedelta
from typing import List
from app.models.entities import Card, PaymentToken
from app.zombie_card_saver.schemas import ZombieSeverity

class ZombieSeverityClassifier:
    """
    Classifies non-fraud lifecycle severity:
    - LOW: Card lifecycle changed, no recent token usage
    - MEDIUM: Active token exists with moderate usage
    - HIGH: Active token has high recent velocity / attempts
    - CRITICAL: Active token + threat exposure / high risk score
    """

    @classmethod
    def classify(cls, card: Card, active_tokens: List[PaymentToken], recent_txn_count: int, exposure_present: bool, risk_score: float) -> ZombieSeverity:
        if exposure_present or risk_score >= 75.0 or (card.status or "").upper() in {"BLOCKED", "COMPROMISED"}:
            return ZombieSeverity.CRITICAL

        if recent_txn_count >= 5 or risk_score >= 40.0:
            return ZombieSeverity.HIGH

        if len(active_tokens) > 0:
            return ZombieSeverity.MEDIUM

        return ZombieSeverity.LOW

zombie_severity_classifier = ZombieSeverityClassifier()
