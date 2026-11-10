import hashlib
import hmac
import json
import os
import time
from unittest.mock import MagicMock, patch
import uuid

from fastapi.testclient import TestClient
import pytest

os.environ["WEBHOOK_SECRET"] = "dummy_webhook_secret"

from backend.api.app import app  # noqa: E402
from backend.llm import chain  # noqa: E402
from backend.llm.providers import (  # noqa: E402
    CloudflareProvider,
    GeminiProvider,
    GroqProvider,
    HuggingFaceRouterProvider,
    NvidiaProvider,
)
from backend.llm.providers.openai_compat import normalize_confidence, parse_json_object  # noqa: E402
from backend.llm.router import RiskLLMRouter  # noqa: E402
from backend.llm.schemas import RiskLLMRequest, RiskLLMResponse  # noqa: E402
from backend.threat_intel import feeds  # noqa: E402

client = TestClient(app)
NEW = [GroqProvider, GeminiProvider, NvidiaProvider, HuggingFaceRouterProvider]


@pytest.fixture
def req():
    return RiskLLMRequest(event_id="ev_1", merchant_id="m1", amount=100.0, currency="INR", risk_level="HIGH",
                          risk_score=95, evidence_summary=[], transaction_context={}, request_type="payment")


def _resp(status=200, body=None):
    m = MagicMock()
    m.status_code = status
    m.json.return_value = body
    if status >= 400:
        import httpx
        m.raise_for_status.side_effect = httpx.HTTPStatusError(str(status), request=MagicMock(), response=m)
    return m


def _choices(content):
    return {"choices": [{"message": {"content": content}}]}


# ── router ──────────────────────────────────────────────────────────────────────────────────

class _Stub:
    def __init__(self, name, status, action=None):
        self.provider_name, self.status, self.action, self.called = name, status, action, False

    def analyze(self, request, timeout=5.0):
        self.called = True
        if self.status == "SUCCESS":
            return RiskLLMResponse(status="SUCCESS", recommended_action=self.action, confidence=80, explanation="x")
        return RiskLLMResponse(status=self.status, explanation="nope")


def test_router_falls_back_past_returned_failures(req):
    a, b, c = _Stub("a", "MISCONFIGURED"), _Stub("b", "UNAVAILABLE"), _Stub("c", "SUCCESS", "REVIEW")
    resp, meta = RiskLLMRouter([a, b, c]).analyze(req)
    assert resp.recommended_action == "REVIEW" and meta["provider"] == "c" and meta["fallback_used"] is True
    assert a.called and b.called


def test_router_total_failure_reports_last_reason(req):
    resp, meta = RiskLLMRouter([_Stub("a", "TIMEOUT"), _Stub("b", "ERROR")]).analyze(req)
    assert resp.status == "ERROR" and meta["status"] == "FAILED" and meta["provider"] is None
    assert meta["failure_reason"] == "b: ERROR"


# ── OpenAI-compatible providers ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cls", NEW)
def test_new_provider_success_with_fenced_json_and_decimal_confidence(cls, req):
    content = 'Here you go:\n```json\n{"recommended_action": "BLOCK", "confidence": 0.9, "explanation": "risk", "cited_evidence_ids": []}\n```'
    with patch("httpx.Client.post", return_value=_resp(200, _choices(content))):
        r = cls(api_key="k").analyze(req)
    assert r.status == "SUCCESS" and r.recommended_action == "BLOCK" and r.confidence == 90 and r.provider == cls.provider_name


@pytest.mark.parametrize("cls", NEW)
@pytest.mark.parametrize("code,status", [(401, "ERROR"), (404, "MISCONFIGURED"), (410, "MISCONFIGURED"), (429, "UNAVAILABLE"), (500, "ERROR")])
def test_new_provider_http_errors(cls, code, status, req):
    with patch("httpx.Client.post", return_value=_resp(code, {})):
        assert cls(api_key="k").analyze(req).status == status


@pytest.mark.parametrize("cls", NEW)
def test_new_provider_rejects_invalid_action_and_missing_key(cls, req):
    bad = '{"recommended_action": "APPROVE_EVERYTHING", "confidence": 50, "explanation": "x", "cited_evidence_ids": []}'
    with patch("httpx.Client.post", return_value=_resp(200, _choices(bad))):
        assert cls(api_key="k").analyze(req).status == "INVALID"
    assert cls(api_key=None).analyze(req).status in ("MISCONFIGURED",) or cls().api_key  # env may supply a key


def test_cloudflare_accepts_openai_shape_with_object_content(req):
    body = {"result": {"choices": [{"message": {"content": {"recommended_action": "REVIEW", "confidence": 70,
                                                             "explanation": "x", "cited_evidence_ids": []}}}]}}
    with patch("httpx.Client.post", return_value=_resp(200, body)):
        r = CloudflareProvider(account_id="a", token="t").analyze(req)
    assert r.status == "SUCCESS" and r.recommended_action == "REVIEW"


def test_hf_token_alias(monkeypatch):
    monkeypatch.delenv("HF_API_KEY", raising=False)
    monkeypatch.setenv("HF_TOKEN", "hf_alias_value")
    assert HuggingFaceRouterProvider().api_key == "hf_alias_value"


def test_json_helpers():
    assert parse_json_object('noise {"a": 1} trailing') == {"a": 1}
    with pytest.raises(json.JSONDecodeError):
        parse_json_object("[1, 2]")
    assert normalize_confidence(0.85) == 85 and normalize_confidence(70.0) == 70 and normalize_confidence(70) == 70


# ── chain, scope, budget ────────────────────────────────────────────────────────────────────

def test_chain_order_from_env_skips_unknown_and_unconfigured(monkeypatch):
    monkeypatch.setenv("NETVRIO_LLM_CHAIN", "groq, bogus, gemini, groq")
    monkeypatch.setenv("GROQ_API_KEY", "k1")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert chain.chain_names() == ["groq", "gemini"]
    assert [p.provider_name for p in chain.build_active()] == ["groq"]


def test_budget_caps_calls_per_minute(monkeypatch):
    monkeypatch.setenv("NETVRIO_LLM_MAX_PER_MIN", "2")
    b = chain.CallBudget()
    assert [b.take(), b.take(), b.take()] == [True, True, False]


def _post(tenant, data):
    payload = {"event_id": f"evt_{uuid.uuid4().hex[:12]}", "merchant_id": tenant, "timestamp": int(time.time()), "data": data}
    body = json.dumps(payload).encode()
    sig = hmac.new(b"dummy_webhook_secret", body, hashlib.sha256).hexdigest()
    return client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": tenant}).json()


def test_flagged_scope_skips_plainly_safe_payments(monkeypatch):
    calls = []
    monkeypatch.setattr("backend.api.routes.webhooks.llm_router.analyze", lambda r: calls.append(r) or (None, {"status": "FAILED"}))
    monkeypatch.setenv("NETVRIO_LLM_SCOPE", "flagged")
    tenant = f"t_scope_{uuid.uuid4().hex[:6]}"
    safe = _post(tenant, {"amount": 100})
    assert safe["ai_advisory"]["status"] == "SKIPPED" and safe["ai_advisory"]["reason"] == "NOT_FLAGGED" and not calls
    risky = _post(tenant, {"amount": 15000})
    assert len(calls) == 1 and risky["decision"] == "REVIEW"


# ── health ──────────────────────────────────────────────────────────────────────────────────

def test_providers_endpoint_lists_chain_without_secrets(monkeypatch):
    monkeypatch.setenv("NETVRIO_LLM_CHAIN", "groq,gemini")
    monkeypatch.setenv("GROQ_API_KEY", "super_secret_value_123")
    body = client.get("/health/providers").json()
    assert [r["name"] for r in body["chain"]] == ["groq", "gemini"]
    assert body["chain"][0]["configured"] is True and body["chain"][0]["status"] == "NOT VERIFIED"
    assert "super_secret_value_123" not in json.dumps(body)


def test_verify_requires_demo_mode_and_records_result(monkeypatch):
    monkeypatch.setenv("NETVRIO_DEMO_MODE", "false")
    assert client.post("/health/providers/verify").status_code == 404
    monkeypatch.setenv("NETVRIO_DEMO_MODE", "true")
    monkeypatch.setenv("NETVRIO_LLM_CHAIN", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    # Stub the provider, not httpx: TestClient is itself an httpx.Client.
    monkeypatch.setattr(GroqProvider, "analyze", lambda self, request, timeout=15.0: RiskLLMResponse(
        status="SUCCESS", recommended_action="REVIEW", confidence=60, explanation="x"))
    body = client.post("/health/providers/verify").json()
    assert body["chain"][0]["status"] == "AVAILABLE" and body["chain"][0]["latency_ms"] is not None


# ── new threat feeds ────────────────────────────────────────────────────────────────────────

def test_feed_parsers():
    assert feeds._parse_feodo('[{"ip_address": "45.95.1.2"}, {"x": 1}]') == ["45.95.1.2"]
    tf = {"query_status": "ok", "data": [{"ioc": "45.95.1.3:443", "ioc_type": "ip:port"}, {"ioc": "evil.example", "ioc_type": "domain"}]}
    assert feeds._parse_threatfox(json.dumps(tf)) == ["45.95.1.3"]
    otx = {"results": [{"indicators": [{"indicator": "45.95.1.4", "type": "IPv4"}, {"indicator": "x.example", "type": "domain"}]}]}
    assert feeds._parse_otx(json.dumps(otx)) == ["45.95.1.4"]


def test_keyed_feeds_inactive_without_key_and_key_only_sent_as_header(monkeypatch):
    spec = next(f for f in feeds.FEEDS if f.state.name == "abusech-threatfox")
    monkeypatch.delenv("ABUSE_CH_AUTH_KEY", raising=False)
    assert spec.active() is False and spec.headers() == {}
    monkeypatch.setenv("ABUSE_CH_AUTH_KEY", "abc")
    assert spec.active() is True and spec.headers() == {"Auth-Key": "abc"} and "abc" not in (spec.state.url or "")
