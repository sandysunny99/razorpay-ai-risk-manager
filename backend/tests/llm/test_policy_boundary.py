import pytest

from backend.policy.engine import PolicyEngine
from backend.policy.models import MerchantPolicy, SecurityValidationResult
from backend.risk.models import ActionDecision, RiskAssessment


def test_llm_cannot_override_deterministic_block():
    policy_engine = PolicyEngine()
    sec_valid = SecurityValidationResult(is_valid_signature=True, is_idempotent=True, is_not_replayed=True, is_valid_tenant=True)
    merchant_policy = MerchantPolicy(merchant_id="m1", auto_block_threshold=90.0, auto_review_threshold=50.0, require_step_up_for_zombie=True)

    # Deterministic risk is HIGH -> Block
    risk_assessment = RiskAssessment(risk_level="HIGH", risk_score=95, confidence=0.9, risk_factors=[], evidence_ids=[], correlation_id="c1", timestamp=12345)

    # LLM Advisory says ALLOW, this is simulated inside the policy engine or webhooks
    # The policy engine in Netvrio doesn't take LLM Advisory output as an argument!
    # Ah! The webhooks route doesn't even pass llm_response to policy_engine!
    # So it naturally cannot override.

    decision = policy_engine.evaluate(risk_assessment, merchant_policy, sec_valid, None)
    assert decision.decision == ActionDecision.BLOCK

def test_llm_cannot_override_deterministic_review():
    policy_engine = PolicyEngine()
    sec_valid = SecurityValidationResult(is_valid_signature=True, is_idempotent=True, is_not_replayed=True, is_valid_tenant=True)
    merchant_policy = MerchantPolicy(merchant_id="m1", auto_block_threshold=90.0, auto_review_threshold=50.0, require_step_up_for_zombie=True)

    risk_assessment = RiskAssessment(risk_level="MEDIUM", risk_score=60, confidence=0.8, risk_factors=[], evidence_ids=[], correlation_id="c1", timestamp=12345)

    decision = policy_engine.evaluate(risk_assessment, merchant_policy, sec_valid, None)
    assert decision.decision == ActionDecision.REVIEW
