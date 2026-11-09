import pytest

from backend.security.card_reference import CardReferenceProtector, ReferenceMode
from backend.security.dlp import redact_sensitive_data


def test_sensitive_data_redaction():
    payload = {
        "pan": "4111111111111111",
        "cvv": "123",
        "nested": {"authorization": "Bearer token123"}
    }
    clean = redact_sensitive_data(payload)
    assert clean["pan"] == "[REDACTED]"
    assert clean["cvv"] == "[REDACTED]"
    assert clean["nested"]["authorization"] == "[REDACTED]"
    assert "4111" not in str(clean)

def test_raw_pan_rejected_in_prod():
    protector = CardReferenceProtector(allow_raw_reference=False)
    with pytest.raises(ValueError):
        protector.normalize("4111111111111111", ReferenceMode.MASKED_REFERENCE)
