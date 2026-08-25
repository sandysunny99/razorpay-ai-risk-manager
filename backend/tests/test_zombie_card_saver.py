import pytest
from datetime import datetime, timedelta
from app.models.entities import Card, PaymentToken, Transaction
from app.zombie_card_saver.detector import zombie_detector
from app.zombie_card_saver.severity import zombie_severity_classifier
from app.zombie_card_saver.impact_analyzer import impact_analyzer
from app.zombie_card_saver.recommendation import zombie_recommender
from app.zombie_card_saver.schemas import ZombieCardStatus, ZombieSeverity, ZombieActionType
from app.zombie_card_saver.service import zombie_card_saver_service
from app.core.database import SessionLocal, Base, engine
from app.db.seed_data import seed_initial_data

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    seed_initial_data(session)
    yield session
    session.close()

def create_test_card(card_id: str, status: str = "ACTIVE", card_fingerprint: str = "fp_test"):
    return Card(
        card_id=card_id,
        customer_id="cust_001",
        masked_pan="**** **** **** 4921",
        card_fingerprint=card_fingerprint,
        bin="453201",
        cardholder_name="Test Cardholder",
        expiry_month=12,
        expiry_year=2024,
        is_expired=(status == "EXPIRED"),
        status=status
    )

def test_zombie_detector_lifecycle_combinations():
    # 1. Healthy Card
    healthy_card = create_test_card("c_healthy", status="ACTIVE", card_fingerprint="fp_1")
    tokens = [PaymentToken(token_id="tok_1", card_id="c_healthy", status="ACTIVE")]
    assert zombie_detector.evaluate_card_zombie_status(healthy_card, tokens) == ZombieCardStatus.HEALTHY

    # 2. Expired Card with Active Token -> ZOMBIE
    expired_card = create_test_card("c_exp", status="EXPIRED", card_fingerprint="fp_2")
    assert zombie_detector.evaluate_card_zombie_status(expired_card, tokens) == ZombieCardStatus.ZOMBIE

    # 3. Blocked Card with Active Token -> CRITICAL
    blocked_card = create_test_card("c_blk", status="BLOCKED", card_fingerprint="fp_3")
    assert zombie_detector.evaluate_card_zombie_status(blocked_card, tokens) == ZombieCardStatus.CRITICAL

    # 4. Expired Card with No Active Tokens -> RESOLVED
    revoked_tokens = [PaymentToken(token_id="tok_rev", card_id="c_exp", status="REVOKED")]
    assert zombie_detector.evaluate_card_zombie_status(expired_card, revoked_tokens) == ZombieCardStatus.RESOLVED

def test_zombie_severity_classification():
    card = create_test_card("c_1", status="EXPIRED", card_fingerprint="fp_1")
    tokens = [PaymentToken(token_id="tok_1", card_id="c_1", status="ACTIVE")]

    # Critical: Exposure present or risk >= 75
    sev_crit = zombie_severity_classifier.classify(card, tokens, recent_txn_count=2, exposure_present=True, risk_score=86.0)
    assert sev_crit == ZombieSeverity.CRITICAL

    # High: Recent velocity >= 5 or risk >= 40
    sev_high = zombie_severity_classifier.classify(card, tokens, recent_txn_count=7, exposure_present=False, risk_score=45.0)
    assert sev_high == ZombieSeverity.HIGH

    # Medium: Active token with low velocity
    sev_med = zombie_severity_classifier.classify(card, tokens, recent_txn_count=1, exposure_present=False, risk_score=20.0)
    assert sev_med == ZombieSeverity.MEDIUM

def test_merchant_impact_and_recurring_protection():
    tok1 = PaymentToken(token_id="tok_sub_netflix", card_id="c_1", merchant_id="m_netflix", status="ACTIVE")
    tok1.is_recurring = True
    tok2 = PaymentToken(token_id="tok_ecom_swiggy", card_id="c_1", merchant_id="m_swiggy", status="ACTIVE")
    tok2.is_recurring = False

    tokens = [tok1, tok2]
    txns = [
        Transaction(txn_id="tx_1", card_id="c_1", customer_id="cust_1", token_id="tok_sub_netflix", amount=649.0, status="SUCCESS"),
        Transaction(txn_id="tx_2", card_id="c_1", customer_id="cust_1", token_id="tok_ecom_swiggy", amount=450.0, status="SUCCESS")
    ]

    impact = impact_analyzer.analyze_merchant_impact(tokens, txns)
    assert impact["affected_merchant_count"] == 2
    assert impact["recurring_subscription_count"] == 1
    assert impact["recent_transaction_volume"] == 1099.0

    # Selective recommendation: High-risk one-off token revoked, recurring subscription token deferred for review
    rec_tok1 = zombie_recommender.recommend_for_token(tok1, card_risk=50.0, is_recurring=True, token_risk=45.0)
    assert rec_tok1 == ZombieActionType.REVIEW

    rec_tok2_high = zombie_recommender.recommend_for_token(tok2, card_risk=80.0, is_recurring=False, token_risk=80.0)
    assert rec_tok2_high == ZombieActionType.REVOKE_TOKEN

@pytest.mark.asyncio
async def test_zombie_service_end_to_end_investigation_and_remediation(db):
    cards = zombie_card_saver_service.get_all_zombie_cards(db)
    assert len(cards) > 0

    stats = zombie_card_saver_service.get_statistics(db)
    assert stats.total_zombie_cards >= 0
    assert stats.verification_success_rate > 90.0

    # Find a card to inspect
    target_card = cards[0]
    analysis = zombie_card_saver_service.get_card_analysis(db, target_card.card_id)
    assert analysis is not None
    assert len(analysis.dependent_tokens) > 0
    assert analysis.audit_hash is not None

    # Test selective token remediation
    target_token = analysis.dependent_tokens[0]
    result = await zombie_card_saver_service.execute_token_remediation(
        db=db,
        token_id=target_token.token_id,
        action=ZombieActionType.REVOKE_TOKEN,
        reason="Test Automated Selective Remediation"
    )
    assert result["success"] is True
    assert result["new_status"] == "REVOKED"
    assert result["audit_block_hash"] is not None
