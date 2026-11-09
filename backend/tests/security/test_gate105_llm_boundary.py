import pytest

from backend.llm.errors import SensitiveDataDetected
from backend.llm.schemas import RiskLLMRequest


def test_llm_boundary_sensitive_data_blocked():
    with pytest.raises(SensitiveDataDetected):
        req = RiskLLMRequest.from_risk_context("e1", "m1", type("obj", (), {"risk_level": type("e", (), {"value": "HIGH"})(), "risk_score": 90})(), type("obj", (), {"items": []})(), {"data": {"card_pan": "4111222233334444"}})
