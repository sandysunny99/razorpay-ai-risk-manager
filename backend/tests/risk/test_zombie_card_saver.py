import pytest

from backend.risk.models import ActionDecision
from backend.risk.zombie_card_saver import CardLifecycle, ZombieCardSaver, ZombieCardSeverity, ZombieRecommendation


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


def test_first_use_of_expired_credential_requires_step_up():
    saver = ZombieCardSaver(allow_raw_reference=True)
    result = saver.analyze("tok_123", "t1", "m_1", {"recent_reuse_count": 0, "card_lifecycle": "EXPIRED"})
    assert "EXPIRED_CARD_REUSE" in result.signals
    assert result.recommendation == ZombieRecommendation.REQUIRE_STEP_UP


def test_replaced_card_token_is_a_zombie():
    saver = ZombieCardSaver(allow_raw_reference=True)
    result = saver.analyze("tok_123", "t1", "m_1", {"recent_reuse_count": 1, "card_lifecycle": "REPLACED"})
    assert "REPLACED_CARD_REUSE" in result.signals
    assert result.recommendation == ZombieRecommendation.REQUIRE_STEP_UP


def test_lifecycle_is_case_insensitive():
    saver = ZombieCardSaver(allow_raw_reference=True)
    result = saver.analyze("tok_123", "t1", "m_1", {"recent_reuse_count": 2, "card_lifecycle": "expired"})
    assert "EXPIRED_CARD_REUSE" in result.signals


def test_sustained_dead_token_reuse_escalates_to_revoke():
    saver = ZombieCardSaver(allow_raw_reference=True)
    high = saver.analyze("tok_123", "t1", "m_1", {"recent_reuse_count": 6, "card_lifecycle": "EXPIRED"})
    assert high.severity == ZombieCardSeverity.HIGH
    assert high.recommendation == ZombieRecommendation.REQUIRE_STEP_UP
    critical = saver.analyze("tok_123", "t1", "m_1", {"recent_reuse_count": 10, "card_lifecycle": "EXPIRED"})
    assert critical.severity == ZombieCardSeverity.CRITICAL
    assert critical.recommendation == ZombieRecommendation.REVOKE_TOKEN


def test_active_card_velocity_is_monitor_only():
    saver = ZombieCardSaver(allow_raw_reference=True)
    result = saver.analyze("tok_123", "t1", "m_1", {"recent_reuse_count": 12, "card_lifecycle": "ACTIVE"})
    assert result.recommendation == ZombieRecommendation.MONITOR
