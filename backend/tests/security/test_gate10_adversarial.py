import pytest

from backend.llm.policy import validate_llm_advisory
from backend.llm.schemas import RiskLLMResponse


def test_gate10_adversarial_unknown_evidence():
    resp = RiskLLMResponse(status="SUCCESS", recommended_action="BLOCK", confidence=90, explanation="t", cited_evidence_ids=["ev_fake"])
    validated = validate_llm_advisory(resp, ["ev_real"])
    assert validated is None
