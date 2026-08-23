import pytest
from app.engines.policy_engine import PolicyEngine, RiskPolicyConfig

def test_policy_token_revocation_auto_execute():
    engine = PolicyEngine()
    # Critical risk: 94.0
    res = engine.evaluate_action("revoke_token", 94.0, {"is_zombie": False})
    assert res["decision"] == "AUTO_EXECUTE"
    assert res["allowed"] is True
    assert res["requires_approval"] is False

def test_policy_token_revocation_zombie():
    engine = PolicyEngine()
    # Even with lower risk score, zombie token triggers auto execute
    res = engine.evaluate_action("revoke_token", 45.0, {"is_zombie": True})
    assert res["decision"] == "AUTO_EXECUTE"
    assert res["allowed"] is True

def test_policy_card_suspension_requires_approval():
    engine = PolicyEngine()
    # Card suspension is high friction - requires human approval
    res = engine.evaluate_action("suspend_card", 95.0, {})
    assert res["decision"] == "REVIEW_REQUIRED"
    assert res["allowed"] is False
    assert res["requires_approval"] is True

def test_policy_financial_transfer_strictly_prohibited():
    engine = PolicyEngine()
    res = engine.evaluate_action("transfer_funds", 99.0, {})
    assert res["decision"] == "NEVER_EXECUTE"
    assert res["allowed"] is False

def test_policy_tier_classification_low_risk():
    engine = PolicyEngine()
    tier = engine.classify_risk_tier(20.0)
    assert tier["risk_level"] == "LOW"
    assert tier["detection_status"] == "CLEAN"
    assert tier["response_tier"] == "LOW"
    assert tier["policy_decision"] == "ALLOW"
    assert tier["recommended_action"] == "ALLOW"
    assert tier["investigation_level"] == 0

def test_policy_tier_classification_monitor():
    engine = PolicyEngine()
    tier = engine.classify_risk_tier(38.0)
    assert tier["risk_level"] == "MEDIUM"
    assert tier["detection_status"] == "CLEAN"
    assert tier["response_tier"] == "MONITOR"
    assert tier["policy_decision"] == "MONITOR"
    assert tier["recommended_action"] == "MONITOR"
    assert tier["investigation_level"] == 1

def test_policy_tier_classification_step_up():
    engine = PolicyEngine()
    tier = engine.classify_risk_tier(54.0)
    assert tier["risk_level"] == "HIGH"
    assert tier["detection_status"] == "SUSPICIOUS"
    assert tier["response_tier"] == "STEP_UP"
    assert tier["policy_decision"] == "STEP_UP_REQUIRED"
    assert tier["recommended_action"] == "REQUEST_STEP_UP"
    assert tier["investigation_level"] == 2

def test_policy_tier_classification_review():
    engine = PolicyEngine()
    tier = engine.classify_risk_tier(70.0)
    assert tier["risk_level"] == "HIGH"
    assert tier["detection_status"] == "SUSPICIOUS"
    assert tier["response_tier"] == "REVIEW"
    assert tier["policy_decision"] == "REVIEW_REQUIRED"
    assert tier["recommended_action"] == "SECURITY_REVIEW"
    assert tier["requires_approval"] is True
    assert tier["investigation_level"] == 2

def test_policy_tier_classification_critical():
    engine = PolicyEngine()
    tier = engine.classify_risk_tier(88.0)
    assert tier["risk_level"] == "CRITICAL"
    assert tier["detection_status"] == "SUSPICIOUS"
    assert tier["response_tier"] == "AUTO_REMEDIATE"
    assert tier["policy_decision"] == "AUTO_EXECUTE"
    assert tier["recommended_action"] == "REVOKE_TOKEN"
    assert tier["requires_approval"] is False
    assert tier["investigation_level"] == 3

def test_policy_step_up_challenge_action_allowed():
    engine = PolicyEngine()
    res = engine.evaluate_action("request_step_up", 55.0, {})
    assert res["decision"] == "AUTO_EXECUTE"
    assert res["allowed"] is True
