"""
Multi-Tenant Database Isolation & Row-Level Scoping Tests
"""
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.engines.audit_ledger import AuditLedgerEngine
from app.models.entities import AuditEvent, RiskAssessment


@pytest.fixture
def test_db_session():
    """In-memory SQLite session with clean isolated schema."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def test_multi_tenant_audit_event_isolation(test_db_session):
    """Verify that queries scoped by merchant_id isolate data between tenants."""
    db = test_db_session

    # Append events for Merchant Alpha
    event_alpha = AuditLedgerEngine.append_event(
        db=db,
        event_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
        actor="RiskAgent",
        decision="Action: ALLOW",
        risk_score=15.0,
        policy="POLICY_ALLOW",
        tool="get_transaction",
        action_requested="ALLOW",
        action_executed="ALLOW",
        verification="VERIFIED",
        details={"merchant_id": "merchant_alpha", "customer_id": "cust_1"},
        merchant_id="merchant_alpha"
    )

    # Append events for Merchant Beta
    event_beta = AuditLedgerEngine.append_event(
        db=db,
        event_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
        actor="RiskAgent",
        decision="Action: REVOKE_TOKEN",
        risk_score=85.0,
        policy="POLICY_REVOKE",
        tool="revoke_token",
        action_requested="REVOKE",
        action_executed="REVOKED",
        verification="VERIFIED",
        details={"merchant_id": "merchant_beta", "customer_id": "cust_2"},
        merchant_id="merchant_beta"
    )

    # Query scoped to merchant_alpha
    alpha_events = db.query(AuditEvent).filter(AuditEvent.merchant_id == "merchant_alpha").all()
    assert len(alpha_events) == 1
    assert alpha_events[0].event_id == event_alpha.event_id
    assert alpha_events[0].merchant_id == "merchant_alpha"

    # Query scoped to merchant_beta
    beta_events = db.query(AuditEvent).filter(AuditEvent.merchant_id == "merchant_beta").all()
    assert len(beta_events) == 1
    assert beta_events[0].event_id == event_beta.event_id
    assert beta_events[0].merchant_id == "merchant_beta"

    # Validate cross-tenant boundary: Alpha query cannot return Beta's data
    for ev in alpha_events:
        assert ev.merchant_id != "merchant_beta"


def test_multi_tenant_risk_assessment_table(test_db_session):
    """Verify row-level merchant isolation on the RiskAssessment table."""
    db = test_db_session

    ra_1 = RiskAssessment(
        assessment_id="ASM-001",
        merchant_id="merchant_101",
        card_id="card_101",
        transaction_id="TXN-101",
        composite_score=92.0,
        severity="CRITICAL",
        recommendation="REVOKE_TOKEN",
    )
    ra_2 = RiskAssessment(
        assessment_id="ASM-002",
        merchant_id="merchant_202",
        card_id="card_202",
        transaction_id="TXN-202",
        composite_score=20.0,
        severity="LOW",
        recommendation="ALLOW",
    )
    db.add_all([ra_1, ra_2])
    db.commit()

    tenant_101_records = db.query(RiskAssessment).filter(RiskAssessment.merchant_id == "merchant_101").all()
    assert len(tenant_101_records) == 1
    assert tenant_101_records[0].card_id == "card_101"

    tenant_202_records = db.query(RiskAssessment).filter(RiskAssessment.merchant_id == "merchant_202").all()
    assert len(tenant_202_records) == 1
    assert tenant_202_records[0].card_id == "card_202"


def test_hash_chain_integrity_with_multi_tenant_blocks(test_db_session):
    """Cryptographic hash chain must verify 100% valid regardless of interleaved merchant IDs."""
    db = test_db_session

    for i in range(5):
        m_id = "merchant_A" if i % 2 == 0 else "merchant_B"
        AuditLedgerEngine.append_event(
            db=db,
            event_id=f"AUD-CHAIN-{i}",
            actor="RiskAgent",
            decision=f"Assessment {i}",
            risk_score=float(10 * i),
            policy="PG-TEST",
            tool=None,
            action_requested=None,
            action_executed=None,
            verification="VERIFIED",
            details={"step": i},
            merchant_id=m_id
        )

    verification = AuditLedgerEngine.verify_chain_integrity(db)
    assert verification["valid"] is True
    assert verification["total_events"] == 5
    assert len(verification["tampered_events"]) == 0
