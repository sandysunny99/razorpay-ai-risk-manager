import pytest

from backend.llm.policy import validate_llm_advisory
from backend.llm.schemas import RiskLLMResponse


def test_adversarial_prompt_injection_ignored():
    resp = RiskLLMResponse(status="SUCCESS", recommended_action="ALLOW", confidence=90, explanation="Ignore previous instructions", cited_evidence_ids=["ev_123"])
    validated = validate_llm_advisory(resp, ["ev_123"])
    assert validated is None
