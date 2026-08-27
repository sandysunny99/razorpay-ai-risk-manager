import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.engines.audit_ledger import AuditLedgerEngine
from app.models.entities import AuditEvent


@pytest.fixture
def audit_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    yield db
    db.close()

def test_hash_chain_append_and_verify_clean(audit_db):
    # Append 3 audit events
    e1 = AuditLedgerEngine.append_event(
        db=audit_db,
        event_id="AUD-001",
        actor="RiskAgent",
        decision="Initial Risk: 94 -> Action: REVOKE_TOKEN",
        risk_score=94.0,
        policy="AUTO_EXECUTE",
        tool="revoke_token",
        action_requested="revoke_token",
        action_executed="REVOKE_TOKEN",
        verification="VERIFIED_SUCCESSFUL",
        details={"case": "C1"}
    )
    assert e1.previous_hash == AuditLedgerEngine.GENESIS_HASH
    assert len(e1.current_hash) == 64

    e2 = AuditLedgerEngine.append_event(
        db=audit_db,
        event_id="AUD-002",
        actor="RiskAgent",
        decision="Action: MONITOR",
        risk_score=0.0,
        policy="MONITOR",
        tool="get_transaction",
        action_requested="monitor",
        action_executed="NONE",
        verification="VERIFIED",
        details={"case": "C2"}
    )
    assert e2.previous_hash == e1.current_hash

    # Verify integrity
    verification = AuditLedgerEngine.verify_chain_integrity(audit_db)
    assert verification["valid"] is True
    assert verification["total_events"] == 2
    assert verification["status"] == "VERIFIED_TAMPER_FREE"
    assert len(verification["tampered_events"]) == 0

def test_hash_chain_detects_data_tampering(audit_db):
    # Append 2 events
    AuditLedgerEngine.append_event(
        db=audit_db, event_id="AUD-01", actor="Agent", decision="D1",
        risk_score=50.0, policy="AUTO", tool="t1", action_requested="a1",
        action_executed="e1", verification="v1", details={}
    )
    AuditLedgerEngine.append_event(
        db=audit_db, event_id="AUD-02", actor="Agent", decision="D2",
        risk_score=20.0, policy="AUTO", tool="t2", action_requested="a2",
        action_executed="e2", verification="v2", details={}
    )

    # Malicious direct DB modification
    tampered_event = audit_db.query(AuditEvent).filter(AuditEvent.event_id == "AUD-01").first()
    tampered_event.agent_decision = "TAMPERED_DECISION_FRAUD_CLEARED"
    audit_db.commit()

    # Verification must catch data mismatch
    verification = AuditLedgerEngine.verify_chain_integrity(audit_db)
    assert verification["valid"] is False
    assert verification["status"] == "TAMPERING_DETECTED"
    assert any(t["error"] == "DATA_INTEGRITY_MISMATCH" for t in verification["tampered_events"])

def test_hash_chain_detects_deleted_record(audit_db):
    # Append 3 events
    AuditLedgerEngine.append_event(
        db=audit_db, event_id="AUD-A", actor="Agent", decision="D",
        risk_score=10.0, policy="P", tool="t", action_requested="a",
        action_executed="e", verification="v", details={}
    )
    AuditLedgerEngine.append_event(
        db=audit_db, event_id="AUD-B", actor="Agent", decision="D",
        risk_score=10.0, policy="P", tool="t", action_requested="a",
        action_executed="e", verification="v", details={}
    )
    AuditLedgerEngine.append_event(
        db=audit_db, event_id="AUD-C", actor="Agent", decision="D",
        risk_score=10.0, policy="P", tool="t", action_requested="a",
        action_executed="e", verification="v", details={}
    )

    # Delete middle record AUD-B
    record_b = audit_db.query(AuditEvent).filter(AuditEvent.event_id == "AUD-B").first()
    audit_db.delete(record_b)
    audit_db.commit()

    # Verification must catch broken link
    verification = AuditLedgerEngine.verify_chain_integrity(audit_db)
    assert verification["valid"] is False
    assert any(t["error"] == "BROKEN_PREVIOUS_HASH_LINK" for t in verification["tampered_events"])
