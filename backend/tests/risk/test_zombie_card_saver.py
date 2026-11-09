import pytest

from backend.risk.models import ActionDecision
from backend.risk.zombie_card_saver import CardLifecycle, ZombieCardSaver, ZombieCardSeverity


def test_normal_card_reuse():
    saver = ZombieCardSaver(allow_raw_reference=True)
    result = saver.analyze("tok_123", "t1", "m_1", {"recent_reuse_count": 2})
    assert result.severity == ZombieCardSeverity.LOW
    assert "HIGH_VELOCITY_REUSE" not in result.signals

def test_suspicious_repeated_reuse():
    saver = ZombieCardSaver(allow_raw_reference=True)
    result = saver.analyze("tok_123", "t1", "m_1", {"recent_reuse_count": 12})
    assert result.severity == ZombieCardSeverity.MEDIUM
    assert "HIGH_VELOCITY_REUSE" in result.signals

def test_expired_inactive_reference():
    saver = ZombieCardSaver(allow_raw_reference=True)
    result = saver.analyze("tok_123", "t1", "m_1", {
        "recent_reuse_count": 1,
        "card_lifecycle": CardLifecycle.EXPIRED
    })
    assert result.severity == ZombieCardSeverity.MEDIUM
    assert "EXPIRED_CARD_REUSE" in result.signals

def test_compromised_reference():
    saver = ZombieCardSaver(allow_raw_reference=True)
    result = saver.analyze("tok_123", "t1", "m_1", {
        "trusted_compromise_assertion": True
    })
    assert result.severity == ZombieCardSeverity.CRITICAL
    assert "COMPROMISED_SOURCE" in result.signals
