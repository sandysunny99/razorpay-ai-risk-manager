import pytest
from app.engines.policy_engine import PolicyEngine

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
