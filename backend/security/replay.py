import time

from backend.security.idempotency import get_idempotency_store

MAX_AGE_SECONDS = 300

def verify_replay(event_id: str, event_timestamp: int, tenant_id: str = "default", max_age: int = MAX_AGE_SECONDS) -> bool:
    """
    Validates timestamp FIRST, then idempotency store.
    """
    current_time = int(time.time())

    # 1. Expired event -> reject
    if current_time - event_timestamp > max_age:
        return False

    # 2. Future event -> reject
    if event_timestamp - current_time > 60:
        return False

    # 3. Previously seen -> reject
    # Note: caller is responsible for registering the event *after* signature validation.
    store = get_idempotency_store()
    if store.has_seen(event_id, tenant_id):
        return False

    return True
