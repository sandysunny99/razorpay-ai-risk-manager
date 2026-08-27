from typing import List

from app.models.entities import Card, PaymentToken
from app.zombie_card_saver.schemas import ZombieCardStatus


class ZombieDetector:
    """
    Detects mismatched credential lifecycle conditions:
    1. EXPIRED_CARD + ACTIVE_TOKEN
    2. BLOCKED_CARD + ACTIVE_TOKEN
    3. REPLACED_CARD + ACTIVE_TOKEN
    4. SUSPENDED_CARD + ACTIVE_TOKEN
    5. COMPROMISED_CARD + ACTIVE_TOKEN
    """

    PROBLEMATIC_CARD_STATES = {"EXPIRED", "BLOCKED", "REPLACED", "SUSPENDED", "COMPROMISED"}

    @classmethod
    def evaluate_card_zombie_status(cls, card: Card, dependent_tokens: List[PaymentToken], exposure_present: bool = False) -> ZombieCardStatus:
        card_state = (card.status or "ACTIVE").upper()
        active_tokens = [t for t in dependent_tokens if (t.status or "ACTIVE").upper() == "ACTIVE"]

        if card_state not in cls.PROBLEMATIC_CARD_STATES:
            return ZombieCardStatus.HEALTHY

        if not active_tokens:
            return ZombieCardStatus.RESOLVED

        # If card is problematic AND has active tokens:
        if exposure_present or card_state in {"BLOCKED", "COMPROMISED"}:
            return ZombieCardStatus.CRITICAL

        if card_state in {"EXPIRED", "REPLACED"}:
            # If recently used, it's ZOMBIE, else AT_RISK
            return ZombieCardStatus.ZOMBIE

        return ZombieCardStatus.AT_RISK

zombie_detector = ZombieDetector()
