import pytest

from backend.policy.engine import PolicyEngine
from backend.policy.models import MerchantPolicy, SecurityValidationResult
from backend.risk.models import ActionDecision, RiskAssessment


def get_base_security() -> SecurityValidationResult:
    return SecurityValidationResult(
        is_valid_signature=True,
        is_idempotent=True,
        is_not_replayed=True,
        is_valid_tenant=True
    )

def test_policy_engine_security_failure():
    engine = PolicyEngine()
    sec_fail = get_base_security()
    sec_fail.is_valid_signature = False

    assessment = RiskAssessment(
        risk_level="LOW", risk_score=10.0, confidence=1.0,
        risk_factors=[], evidence_ids=["evt_1"], correlation_id="c_1", timestamp=12345
    )
    policy = MerchantPolicy(merchant_id="m_1", auto_block_threshold=90.0, auto_review_threshold=50.0, require_step_up_for_zombie=True)

    result = engine.evaluate(assessment, policy, sec_fail)
    assert result.decision == ActionDecision.BLOCK
    assert "SECURITY_VALIDATION_FAILED" in result.reason_codes

def test_policy_engine_zombie_block():
    engine = PolicyEngine()
    assessment = RiskAssessment(
        risk_level="LOW", risk_score=10.0, confidence=1.0,
        risk_factors=[], evidence_ids=["evt_1"], correlation_id="c_1", timestamp=12345
    )
    policy = MerchantPolicy(merchant_id="m_1", auto_block_threshold=90.0, auto_review_threshold=50.0, require_step_up_for_zombie=True)

    result = engine.evaluate(assessment, policy, get_base_security(), zombie_remediation=ActionDecision.BLOCK)
    assert result.decision == ActionDecision.BLOCK
    assert "ZOMBIE_CARD_CRITICAL" in result.reason_codes

def test_policy_engine_risk_thresholds():
    engine = PolicyEngine()
    policy = MerchantPolicy(merchant_id="m_1", auto_block_threshold=90.0, auto_review_threshold=50.0, require_step_up_for_zombie=True)

    # Allow
    assessment_allow = RiskAssessment(
        risk_level="LOW", risk_score=10.0, confidence=1.0,
        risk_factors=[], evidence_ids=["evt_1"], correlation_id="c_1", timestamp=12345
    )
    result = engine.evaluate(assessment_allow, policy, get_base_security())
    assert result.decision == ActionDecision.ALLOW

    # Review
    assessment_review = RiskAssessment(
        risk_level="MEDIUM", risk_score=60.0, confidence=1.0,
        risk_factors=[], evidence_ids=["evt_1"], correlation_id="c_1", timestamp=12345
    )
    result = engine.evaluate(assessment_review, policy, get_base_security())
    assert result.decision == ActionDecision.REVIEW
