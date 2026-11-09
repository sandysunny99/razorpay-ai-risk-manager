from unittest.mock import MagicMock, patch

import pytest

from backend.llm.providers.cloudflare import CloudflareProvider
from backend.llm.providers.grok import GrokProvider
from backend.llm.providers.huggingface import HuggingFaceProvider
from backend.llm.schemas import RiskLLMRequest


@pytest.fixture
def mock_req():
    return RiskLLMRequest(
        event_id="ev_1",
        merchant_id="m1",
        amount=100.0,
        currency="USD",
        risk_level="HIGH",
        risk_score=95,
        risk_features={"f1": True},
        evidence_summary=["no secrets here"],
        evidence_package_id="ev_pkg_123",
        transaction_context={"ip": "1.1.1.1"},
        request_type="payment"
    )

PROVIDERS = [
    (CloudflareProvider, "cloudflare"),
    (GrokProvider, "grok"),
    (HuggingFaceProvider, "huggingface")
]

@pytest.mark.parametrize("provider_class, provider_name", PROVIDERS)
def test_outgoing_payload_safety(provider_class, provider_name, mock_req):
    with patch(f'backend.llm.providers.{provider_name}.httpx.Client.post') as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        # Valid JSON response shape depending on provider
        if provider_name == "cloudflare":
            mock_resp.json.return_value = {"result": {"response": '{"recommended_action": "BLOCK", "confidence": 99, "explanation": "Risk", "cited_evidence_ids": ["ev_pkg_123"]}'}}
        elif provider_name == "grok":
            mock_resp.json.return_value = {"choices": [{"message": {"content": '{"recommended_action": "BLOCK", "confidence": 99, "explanation": "Risk", "cited_evidence_ids": ["ev_pkg_123"]}'}}]}
        else:
            mock_resp.json.return_value = [{"generated_text": '{"recommended_action": "BLOCK", "confidence": 99, "explanation": "Risk", "cited_evidence_ids": ["ev_pkg_123"]}'}]

        mock_post.return_value = mock_resp

        if provider_class == CloudflareProvider:
            provider = provider_class(account_id="acc123", token="tok123")
        else:
            provider = provider_class(api_key="key123")

        provider.analyze(mock_req)

        call_args = mock_post.call_args
        req_json = call_args.kwargs["json"]

        # Extract prompt content
        if provider_name in ["cloudflare", "grok"]:
            prompt_content = req_json["messages"][1]["content"]
        else:
            prompt_content = req_json["inputs"]

        # Verify allowed context is present
        assert "Risk Score: 95" in prompt_content
        assert "Amount: 100.0 USD" in prompt_content
        assert "ev_pkg_123" in prompt_content

        # Verify no sensitive data
        lower_prompt = prompt_content.lower()
        forbidden_terms = ["card_pan", "cvv", "pin", "api_key", "jwt", "authorization", "password"]
        for term in forbidden_terms:
            assert term not in lower_prompt
