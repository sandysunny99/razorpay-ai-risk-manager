from unittest.mock import MagicMock, patch

import httpx
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
        evidence_summary=[],
        transaction_context={},
        request_type="payment"
    )

PROVIDERS = [
    (CloudflareProvider, "cloudflare", '{"result": {"response": "{PAYLOAD}"}}'),
    (GrokProvider, "grok", '{"choices": [{"message": {"content": "{PAYLOAD}"}}]}'),
    (HuggingFaceProvider, "huggingface", '[{"generated_text": "{PAYLOAD}"}]')
]

@pytest.mark.parametrize("provider_class, name, response_template", PROVIDERS)
class TestAllProviders:
    def get_provider(self, provider_class):
        if provider_class == CloudflareProvider:
            return provider_class(account_id="acc1", token="tok1")
        elif provider_class == GrokProvider:
            return provider_class(api_key="key1")
        else:
            return provider_class(api_key="key1")

    def mock_post(self, mocker, provider_class, status_code=200, payload_str=None):
        if payload_str is None:
            payload_str = '{"recommended_action": "BLOCK", "confidence": 99, "explanation": "Risk", "cited_evidence_ids": []}'

        # If payload_str is literal 'not json', we need to format it into the template, but carefully so it doesn't break python JSON loading
        # Wait, the template expects to be evaluated as a dict eventually because the providers call resp.json()
        pass

# Instead of a class, let's use a function that generates a mock response dict based on the provider
def make_mock_json(provider_name, inner_payload_str):
    import json
    if provider_name == "cloudflare":
        return {"result": {"response": inner_payload_str}}
    elif provider_name == "grok":
        return {"choices": [{"message": {"content": inner_payload_str}}]}
    else:
        return [{"generated_text": inner_payload_str}]

def run_test(provider_class, provider_name, mock_req, mocker, inner_payload_str=None, status_code=200, exc=None):
    if provider_class == CloudflareProvider:
        provider = provider_class(account_id="acc1", token="tok1")
    else:
        provider = provider_class(api_key="key1")

    with patch(f'backend.llm.providers.{provider_name}.httpx.Client.post') as mock_post:
        if exc:
            mock_post.side_effect = exc
        else:
            mock_resp = MagicMock()
            mock_resp.status_code = status_code
            if inner_payload_str is not None:
                mock_resp.json.return_value = make_mock_json(provider_name, inner_payload_str)
            if status_code >= 400:
                mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(f"{status_code}", request=MagicMock(), response=mock_resp)
            mock_post.return_value = mock_resp

        return provider.analyze(mock_req)

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_200_valid(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, '{"recommended_action": "BLOCK", "confidence": 99, "explanation": "Risk", "cited_evidence_ids": []}')
    assert resp.status == "SUCCESS"
    assert resp.recommended_action == "BLOCK"
    assert resp.provider == name

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_200_malformed_json(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, 'not valid json')
    assert resp.status == "INVALID"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_invalid_action(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, '{"recommended_action": "IGNORE", "confidence": 99, "explanation": "Risk", "cited_evidence_ids": []}')
    assert resp.status == "INVALID"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_invalid_confidence_low(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, '{"recommended_action": "BLOCK", "confidence": -1, "explanation": "Risk", "cited_evidence_ids": []}')
    assert resp.status == "INVALID"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_invalid_confidence_high(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, '{"recommended_action": "BLOCK", "confidence": 101, "explanation": "Risk", "cited_evidence_ids": []}')
    assert resp.status == "INVALID"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_invalid_confidence_string(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, '{"recommended_action": "BLOCK", "confidence": "high", "explanation": "Risk", "cited_evidence_ids": []}')
    assert resp.status == "INVALID"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_missing_structure(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, '{"confidence": 99}')
    assert resp.status == "INVALID"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_malformed_cited_evidence(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, '{"recommended_action": "BLOCK", "confidence": 99, "explanation": "Risk", "cited_evidence_ids": "ev_1"}') # Should be a list
    assert resp.status == "INVALID"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_401(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, status_code=401)
    assert resp.status == "ERROR"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_403(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, status_code=403)
    assert resp.status == "ERROR"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_429(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, status_code=429)
    assert resp.status == "UNAVAILABLE"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_500(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, status_code=500)
    assert resp.status == "ERROR"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_timeout(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, exc=httpx.TimeoutException("timeout"))
    assert resp.status == "TIMEOUT"

@pytest.mark.parametrize("provider_class, name", [(CloudflareProvider, "cloudflare"), (GrokProvider, "grok"), (HuggingFaceProvider, "huggingface")])
def test_connection_failure(provider_class, name, mock_req):
    resp = run_test(provider_class, name, mock_req, None, exc=httpx.RequestError("conn failed"))
    assert resp.status == "UNAVAILABLE"

