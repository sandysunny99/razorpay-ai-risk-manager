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

STEP_UP_VELOCITY_THRESHOLD = 5   # > 5 reuses in 24h: high-velocity reuse
REVOKE_REUSE_THRESHOLD = 10      # >= 10 reuses of a dead credential in 24h: revoke the token


class ZombieCardSaver:
    def __init__(self, allow_raw_reference: bool = False):
        self.protector = CardReferenceProtector(allow_raw_reference=allow_raw_reference)

    def analyze(self, token_reference: str, tenant_id: str, merchant_id: str, event_data: Dict[str, Any]) -> ZombieRiskAssessment:
        normalized_ref = self.protector.normalize(token_reference, ReferenceMode.MASKED_REFERENCE) # Just for display in the analysis result

        signals = []
        raw_lifecycle = event_data.get("card_lifecycle") or CardLifecycle.ACTIVE
        # Enum members must use .value: str(Enum) is "CardLifecycle.EXPIRED" on Python 3.11+.
        lifecycle = str(getattr(raw_lifecycle, "value", raw_lifecycle)).upper()
        reuse_count = int(event_data.get("recent_reuse_count") or 0)
        dead_credential = lifecycle in (CardLifecycle.EXPIRED.value, CardLifecycle.REPLACED.value)

        # Explicit trusted security assertions vs observed signals
        trusted_compromise_signal = event_data.get("trusted_compromise_assertion", False)

        if event_data.get("token_revoked"):
            # Remediation enforcement: a token previously revoked by Zombie Card Saver is back.
            signals.append("REVOKED_TOKEN_REUSE")
            severity = ZombieCardSeverity.CRITICAL
            rec = ZombieRecommendation.REVOKE_TOKEN
            impact = "Revoked token presented again"
        elif trusted_compromise_signal:
            signals.append("COMPROMISED_SOURCE")
            severity = ZombieCardSeverity.CRITICAL
            rec = ZombieRecommendation.REVOKE_TOKEN
            impact = "Known compromised card attempted reuse"
        elif dead_credential:
            # A token that outlives its card (expired or replaced) is the zombie case. Presenting it
            # at all needs step-up; sustained reuse means the token itself must be revoked.
            signals.append(f"{lifecycle}_CARD_REUSE")
            if reuse_count >= REVOKE_REUSE_THRESHOLD:
                signals.append("HIGH_VELOCITY_REUSE")
                severity = ZombieCardSeverity.CRITICAL
                rec = ZombieRecommendation.REVOKE_TOKEN
                impact = f"Dead credential reused {reuse_count} times in 24h"
            elif reuse_count > STEP_UP_VELOCITY_THRESHOLD:
                signals.append("HIGH_VELOCITY_REUSE")
                severity = ZombieCardSeverity.HIGH
                rec = ZombieRecommendation.REQUIRE_STEP_UP
                impact = "High reuse velocity detected"
            else:
                severity = ZombieCardSeverity.MEDIUM
                rec = ZombieRecommendation.REQUIRE_STEP_UP
                impact = f"{lifecycle.capitalize()} card credential presented"
        elif reuse_count > STEP_UP_VELOCITY_THRESHOLD:
            # Busy but valid card: worth watching, not a zombie, so no policy effect.
            signals.append("HIGH_VELOCITY_REUSE")
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
