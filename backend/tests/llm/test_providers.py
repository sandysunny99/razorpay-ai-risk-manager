from unittest.mock import MagicMock, patch

import pytest

from backend.llm.health import ProviderHealthState
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
        evidence_summary=[],
        transaction_context={},
        request_type="payment"
    )

def test_cloudflare_provider_no_credentials(mock_req):
    provider = CloudflareProvider(account_id=None, token=None)
    assert provider.health().state == ProviderHealthState.NOT_VERIFIED
    resp = provider.analyze(mock_req)
    assert resp.status == "MISCONFIGURED"
    assert resp.recommended_action is None

def test_grok_provider_no_credentials(mock_req):
    provider = GrokProvider(api_key=None)
    assert provider.health().state == ProviderHealthState.NOT_VERIFIED
    resp = provider.analyze(mock_req)
    assert resp.status == "MISCONFIGURED"

def test_hf_provider_no_credentials(mock_req):
    provider = HuggingFaceProvider(api_key=None)
    assert provider.health().state == ProviderHealthState.NOT_VERIFIED
    resp = provider.analyze(mock_req)
    assert resp.status == "MISCONFIGURED"

@patch('backend.llm.providers.cloudflare.httpx.Client.post')
def test_cloudflare_provider_success(mock_post, mock_req):
    # Setup mock response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "response": '{"recommended_action": "BLOCK", "confidence": 99, "explanation": "Risk", "cited_evidence_ids": []}'
        }
    }
    mock_post.return_value = mock_resp

    provider = CloudflareProvider(account_id="acc123", token="tok123")
    resp = provider.analyze(mock_req)

    assert resp.status == "SUCCESS"
    assert resp.recommended_action == "BLOCK"
    assert resp.confidence == 99

    # Verify request payload
    call_args = mock_post.call_args
    assert "tok123" in call_args.kwargs["headers"]["Authorization"]
    req_json = call_args.kwargs["json"]
    assert req_json["messages"][1]["content"].startswith("Analyze this transaction.")

@patch('backend.llm.providers.grok.httpx.Client.post')
def test_grok_provider_rate_limit(mock_post, mock_req):
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_post.return_value = mock_resp

    provider = GrokProvider(api_key="key123")
    resp = provider.analyze(mock_req)
    assert resp.status == "UNAVAILABLE"
    assert "Rate limit" in resp.explanation

@patch('backend.llm.providers.huggingface.httpx.Client.post')
def test_hf_provider_invalid_json(mock_post, mock_req):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"generated_text": "I am not JSON at all."}]
    mock_post.return_value = mock_resp

    provider = HuggingFaceProvider(api_key="key123")
    resp = provider.analyze(mock_req)
    assert resp.status == "INVALID"
    assert "parse" in resp.explanation
