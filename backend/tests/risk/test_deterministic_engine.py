import pytest

from backend.risk.engine import DeterministicRiskEngine


def test_deterministic_engine_low_risk():
    engine = DeterministicRiskEngine()
    event_data = {
        "event_id": "evt_100",
        "amount": 50.0,
        "merchant_id": "m_1",
        "customer_id": "c_1"
    }

    assessment = engine.analyze(event_data, correlation_id="corr_1")
    assert assessment.risk_level == "LOW"
    assert assessment.risk_score == 0.0
    assert len(assessment.risk_factors) == 0
    assert assessment.correlation_id == "corr_1"

def test_deterministic_engine_high_risk():
    engine = DeterministicRiskEngine()
    event_data = {
        "event_id": "evt_101",
        "amount": 15000.0,
        "merchant_id": "m_1",
        "customer_id": "c_1"
    }

    assessment = engine.analyze(event_data, correlation_id="corr_2")
    assert assessment.risk_level == "MEDIUM" or assessment.risk_level == "HIGH"
    assert assessment.risk_score == 50.0
    assert len(assessment.risk_factors) == 1
    assert assessment.risk_factors[0].name == "high_amount"
