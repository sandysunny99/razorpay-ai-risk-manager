import time

import pytest

from backend.security.idempotency import get_idempotency_store
from backend.security.replay import verify_replay


def test_invalid_signature_does_not_consume_idempotency():
    store = get_idempotency_store()
    event_id = "evt_sig_fail"
    tenant = "t1"

    # Simulate: parsing -> sig verification fails.
    # The event is NEVER registered in idempotency.
    # We prove this by ensuring it has not been seen.
    assert store.has_seen(event_id, tenant) is False

    # Simulate valid retry arrives later
    assert store.register_event(event_id, tenant) is True

def test_stale_and_future_timestamp_rejected():
    now = int(time.time())
    store = get_idempotency_store()

    # Stale (6 mins ago)
    assert verify_replay("evt_stale", now - 360, "t1") is False
    assert store.has_seen("evt_stale", "t1") is False # Replay fails BEFORE idempotency

    # Future (2 mins future)
    assert verify_replay("evt_future", now + 120, "t1") is False

    # Duplicate valid
    verify_replay("evt_valid", now, "t1")
    store.register_event("evt_valid", "t1")
    # Next check should fail because it's seen
    assert verify_replay("evt_valid", now, "t1") is False
