import time
from typing import Any, Dict, List

from backend.risk.features import extract_features
from backend.risk.models import RiskAssessment, RiskFactor
from backend.risk.rules import evaluate_amount, evaluate_velocity


class DeterministicRiskEngine:
    def analyze(self, event_data: Dict[str, Any], correlation_id: str) -> RiskAssessment:
        features = extract_features(event_data)

        factors: List[RiskFactor] = []

        factor_amount = evaluate_amount(features['amount'])
        if factor_amount.score_impact > 0:
            factors.append(factor_amount)

        factor_velocity = evaluate_velocity(features['velocity_1h'])
        if factor_velocity.score_impact > 0:
            factors.append(factor_velocity)

        total_score = min(100.0, sum(f.score_impact for f in factors))
        risk_level = "HIGH" if total_score >= 70.0 else "MEDIUM" if total_score >= 30.0 else "LOW"

        return RiskAssessment(
            risk_level=risk_level,
            risk_score=total_score,
            confidence=1.0,  # Deterministic has high confidence
            risk_factors=factors,
            evidence_ids=[event_data.get('event_id', 'unknown')],
            correlation_id=correlation_id,
            timestamp=int(time.time())
        )
