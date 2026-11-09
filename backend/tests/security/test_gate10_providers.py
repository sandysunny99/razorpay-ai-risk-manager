import pytest

from backend.llm.providers.cloudflare import CloudflareProvider
from backend.llm.providers.grok import GrokProvider
from backend.llm.providers.huggingface import HuggingFaceProvider
from backend.llm.router import RiskLLMRouter
from backend.llm.schemas import RiskLLMRequest


def test_provider_registry_returns_unavailable():
    registry = RiskLLMRouter([CloudflareProvider(), GrokProvider(), HuggingFaceProvider()])
    req = RiskLLMRequest(event_id="e1", merchant_id="m1", amount=10.0, currency="USD", risk_level="LOW", risk_score=10, evidence_summary=[])
    result, meta = registry.analyze(req)
    assert result.status == "MISCONFIGURED"  # Architectural change: router now returns a structured RiskLLMResponse on total failure rather than None
