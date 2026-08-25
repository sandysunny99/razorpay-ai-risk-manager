import time
from typing import Dict, Optional
import threading

class EventDeduplicator:
    """
    In-memory thread-safe TTL idempotency tracker.
    Prevents duplicate event ingestion across webhooks and telemetry streams.
    """
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 50000):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, float] = {}
        self._lock = threading.Lock()

    def is_duplicate(self, idempotency_key: str) -> bool:
        if not idempotency_key:
            return False
        
        now = time.time()
        with self._lock:
            # Purge expired entries if cache is growing
            if len(self._cache) > self.max_size:
                self._purge_expired(now)

            if idempotency_key in self._cache:
                expiry = self._cache[idempotency_key]
                if now < expiry:
                    return True
                else:
                    del self._cache[idempotency_key]

            # Register key with expiry
            self._cache[idempotency_key] = now + self.ttl_seconds
            return False

    def _purge_expired(self, now: float):
        expired_keys = [k for k, exp in self._cache.items() if exp <= now]
        for k in expired_keys:
            del self._cache[k]

    def clear(self):
        with self._lock:
            self._cache.clear()

event_deduplicator = EventDeduplicator()
