import pytest

from backend.llm.errors import SensitiveDataDetected
from backend.llm.schemas import RiskLLMRequest


def test_recursive_sensitive_data_check():
    # 1. Nested PAN key
    payload = {
        "event_id": "ev_1",
        "merchant_id": "m1",
        "amount": 10.0,
        "currency": "USD",
        "risk_level": "LOW",
        "risk_score": 10,
        "evidence_summary": [],
        "risk_features": {
            "metadata": {
                "card_pan": "1234"
            }
        }
    }
    with pytest.raises(SensitiveDataDetected, match="Forbidden key 'card_pan'"):
        RiskLLMRequest(**payload)

    # 2. Nested CVV key in transaction_context
    payload["risk_features"] = None
    payload["transaction_context"] = {
        "metadata": {
            "cvv": "123"
        }
    }
    with pytest.raises(SensitiveDataDetected, match="Forbidden key 'cvv'"):
        RiskLLMRequest(**payload)

    # 3. Nested string containing PAN-like substring
    payload["transaction_context"] = {
        "metadata": {
            "safe_key": "some text 4111 2222 3333 4444 here"
        }
    }
    with pytest.raises(SensitiveDataDetected, match="Potential secret or PAN detected"):
        RiskLLMRequest(**payload)

    # 4. Nested list containing JWT-like string
    payload["transaction_context"] = None
    payload["evidence_summary"] = [
        "Normal evidence",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    ]
    with pytest.raises(SensitiveDataDetected, match="Potential JWT detected"):
        RiskLLMRequest(**payload)

    # 5. Clean payload should pass
    payload["evidence_summary"] = ["All good"]
    req = RiskLLMRequest(**payload)
    assert req.event_id == "ev_1"
