import pytest

from app.engines.nlp_classifier import NLPClassifier


def test_nlp_classifier_initialization():
    """NLPClassifier initializes cleanly without raising exceptions."""
    classifier = NLPClassifier()
    assert isinstance(classifier.available, bool)


@pytest.mark.asyncio
async def test_classify_threat_text_returns_valid_or_none():
    """classify_threat_text returns valid dict or None, never raises."""
    classifier = NLPClassifier()
    result = await classifier.classify_threat_text("test stealer dump credential")
    assert result is None or (
        isinstance(result, dict)
        and "label" in result
        and "confidence" in result
        and 0.0 <= result["confidence"] <= 1.0
    )


@pytest.mark.asyncio
async def test_extract_dlp_entities_returns_valid_or_none():
    """extract_dlp_entities returns valid list or None, never raises."""
    classifier = NLPClassifier()
    result = await classifier.extract_dlp_entities("My card 4111 1111 1111 1111 was used")
    assert result is None or isinstance(result, list)


@pytest.mark.asyncio
async def test_summarize_audit_events_returns_valid_or_none():
    """summarize_audit_events returns str or None, never raises."""
    classifier = NLPClassifier()
    events = [{"event_type": "TRANSACTION_BLOCKED", "risk_score": 94}]
    result = await classifier.summarize_audit_events(events)
    assert result is None or isinstance(result, str)
