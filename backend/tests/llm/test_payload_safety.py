import pytest

from backend.llm.health import ProviderHealth, ProviderHealthState
from backend.llm.interfaces import RiskLLMProvider
from backend.llm.router import RiskLLMRouter
from backend.llm.schemas import RiskLLMRequest, RiskLLMResponse


class CaptureMockProvider(RiskLLMProvider):
    provider_name = "CaptureMock"

    def __init__(self):
        self.captured_payload = None

    def analyze(self, request: RiskLLMRequest, timeout: float = 5.0) -> RiskLLMResponse:
        # Capture exactly what would be serialized and sent to the remote API
        self.captured_payload = request.model_dump()
        return RiskLLMResponse(status="SUCCESS", recommended_action="ALLOW", confidence=99, explanation="Safe", cited_evidence_ids=[])

    def health(self) -> ProviderHealth:
        return ProviderHealth(self.provider_name, ProviderHealthState.AVAILABLE)

def test_provider_payload_safety():
    provider = CaptureMockProvider()
    router = RiskLLMRouter([provider])

    req = RiskLLMRequest(
        event_id="ev_1",
        merchant_id="m1",
        amount=10.0,
        currency="USD",
        risk_level="LOW",
        risk_score=10,
        risk_features={"f1": True},
        evidence_summary=["no secrets here"],
        transaction_context={"ip": "1.1.1.1"}
    )

    resp, meta = router.analyze(req)
    assert resp.status == "SUCCESS"
    assert provider.captured_payload is not None

    # Verify ONLY permitted fields exist in the serialized outgoing payload
    allowed_keys = {
        "event_id", "merchant_id", "amount", "currency",
        "risk_level", "risk_score", "risk_features",
        "zombie_signal", "evidence_package_id", "evidence_summary",
        "transaction_context", "request_type", "zombie_severity"
    }

    for key in provider.captured_payload.keys():
        assert key in allowed_keys

    # Verify forbidden keys are completely absent from nested dicts
    def recursive_key_check(d):
        if isinstance(d, dict):
            for k, v in d.items():
                assert k.lower() not in {"card_pan", "cvv", "pin", "api_key", "secret", "password", "token", "jwt", "authorization"}
                recursive_key_check(v)
        elif isinstance(d, list):
            for i in d:
                recursive_key_check(i)

    recursive_key_check(provider.captured_payload)
