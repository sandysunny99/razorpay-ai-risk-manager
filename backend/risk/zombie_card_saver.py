from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from backend.security.card_reference import CardReferenceProtector, ReferenceMode


class CardLifecycle(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REPLACED = "REPLACED"

class ZombieCardSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ZombieRecommendation(str, Enum):
    MONITOR = "MONITOR"
    REQUIRE_STEP_UP = "REQUIRE_STEP_UP"
    REVOKE_TOKEN = "REVOKE_TOKEN"

class ZombieRiskAssessment(BaseModel):
    tenant_id: str
    merchant_id: str
    reference_id: str
    case_id: Optional[str]
    evidence_ids: List[str]
    signals: List[str]
    severity: ZombieCardSeverity
    impact: str
    recommendation: ZombieRecommendation

class ZombieCardSaver:
    def __init__(self, allow_raw_reference: bool = False):
        self.protector = CardReferenceProtector(allow_raw_reference=allow_raw_reference)

    def analyze(self, token_reference: str, tenant_id: str, merchant_id: str, event_data: Dict[str, Any]) -> ZombieRiskAssessment:
        normalized_ref = self.protector.normalize(token_reference, ReferenceMode.MASKED_REFERENCE) # Just for display in the analysis result

        signals = []
        lifecycle = event_data.get("card_lifecycle", CardLifecycle.ACTIVE)
        reuse_count = event_data.get("recent_reuse_count", 0)

        # Explicit trusted security assertions vs observed signals
        trusted_compromise_signal = event_data.get("trusted_compromise_assertion", False)

        if trusted_compromise_signal:
            signals.append("COMPROMISED_SOURCE")
            severity = ZombieCardSeverity.CRITICAL
            rec = ZombieRecommendation.REVOKE_TOKEN
            impact = "Known compromised card attempted reuse"
        else:
            if lifecycle == CardLifecycle.EXPIRED and reuse_count > 0:
                signals.append("EXPIRED_CARD_REUSE")
            if reuse_count > 5:
                signals.append("HIGH_VELOCITY_REUSE")

            if "EXPIRED_CARD_REUSE" in signals and "HIGH_VELOCITY_REUSE" in signals:
                severity = ZombieCardSeverity.HIGH
                rec = ZombieRecommendation.REQUIRE_STEP_UP
                impact = "High reuse velocity detected"
            elif signals:
                severity = ZombieCardSeverity.MEDIUM
                rec = ZombieRecommendation.MONITOR
                impact = "Anomalous reuse pattern"
            else:
                severity = ZombieCardSeverity.LOW
                rec = ZombieRecommendation.MONITOR
                impact = "Normal usage"

        return ZombieRiskAssessment(
            tenant_id=tenant_id,
            merchant_id=merchant_id,
            reference_id=normalized_ref,
            case_id=None,
            evidence_ids=[event_data.get('event_id', 'unknown')],
            signals=signals,
            severity=severity,
            impact=impact,
            recommendation=rec
        )
