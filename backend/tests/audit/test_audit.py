
import pytest

from backend.audit.audit_log import AuditRecordModel, SqlAuditRepository


def test_audit_chain():
    store = SqlAuditRepository("sqlite:///:memory:")
    h1 = store.append_record({"audit_id": "a1", "decision": "ALLOW", "event_id": "1"})
    h2 = store.append_record({"audit_id": "a2", "decision": "BLOCK", "event_id": "2"})
    assert store.verify_chain() is True

    # Tamper
    with store.Session() as session:
        record = session.query(AuditRecordModel).first()
        record.record_payload = {"decision": "TAMPERED", "event_id": "1"}
        session.commit()

    assert store.verify_chain() is False
