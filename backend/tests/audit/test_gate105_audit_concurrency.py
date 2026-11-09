import threading

import pytest

from backend.audit.audit_log import SqlAuditRepository


def append_worker(repo, event_id):
    repo.append_record({
        "audit_id": f"aud_{event_id}",
        "event_id": event_id,
        "merchant_id": "m1",
        "correlation_id": "c1",
        "timestamp": 123,
        "record_type": "decision",
        "decision": "ALLOW",
        "reason_codes": []
    })

def test_sql_audit_concurrency():
    repo = SqlAuditRepository("sqlite:///:memory:") # In-memory SQLite for test
    threads = []

    # Spawn 10 concurrent threads to append records
    for i in range(10):
        t = threading.Thread(target=append_worker, args=(repo, f"evt_{i}"))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert repo.verify_chain() is True
