from abc import ABC, abstractmethod
import os
import threading
import time
from typing import Dict

import redis

from backend.runtime_env import is_test_env


class IdempotencyStore(ABC):
    @abstractmethod
    def register_event(self, event_id: str, tenant_id: str) -> bool:
        pass
    @abstractmethod
    def has_seen(self, event_id: str, tenant_id: str) -> bool:
        pass
    @abstractmethod
    def is_available(self) -> bool:
        pass

class InMemoryIdempotencyStore(IdempotencyStore):
    """Single-process store. Bounded: keys older than RETENTION_S are pruned once MAX_KEYS is hit.
    Retention is far longer than the 300 s replay window, so pruning never re-opens a replay."""
    MAX_KEYS = 200_000
    RETENTION_S = 24 * 3600

    def __init__(self):
        self._events: Dict[str, float] = {}
        self._lock = threading.Lock()
    def _key(self, event_id: str, tenant_id: str) -> str:
        return f"{tenant_id}:{event_id}"
    def register_event(self, event_id: str, tenant_id: str) -> bool:
        key = self._key(event_id, tenant_id)
        with self._lock:
            if key in self._events:
                return False
            if len(self._events) >= self.MAX_KEYS:
                cutoff = time.time() - self.RETENTION_S
                self._events = {k: t for k, t in self._events.items() if t >= cutoff}
            self._events[key] = time.time()
            return True
    def has_seen(self, event_id: str, tenant_id: str) -> bool:
        key = self._key(event_id, tenant_id)
        with self._lock:
            return key in self._events
    def is_available(self) -> bool:
        return True

class RedisIdempotencyStore(IdempotencyStore):
    def __init__(self, redis_url: str, ttl_seconds: int = 86400):
        self.ttl = ttl_seconds
        try:
            self.client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.client.ping()
            self._available = True
        except Exception:
            self._available = False
            self.client = None

    def _key(self, event_id: str, tenant_id: str) -> str:
        return f"netvrio:idempotency:{tenant_id}:{event_id}"

    def register_event(self, event_id: str, tenant_id: str) -> bool:
        if not self._available:
            raise ConnectionError("Redis is unavailable")
        key = self._key(event_id, tenant_id)
        # SET NX EX is atomic
        result = self.client.set(key, "1", nx=True, ex=self.ttl)
        return bool(result)

    def has_seen(self, event_id: str, tenant_id: str) -> bool:
        if not self._available:
            raise ConnectionError("Redis is unavailable")
        return bool(self.client.exists(self._key(event_id, tenant_id)))

    def is_available(self) -> bool:
        return self._available

_in_memory_store = InMemoryIdempotencyStore()
_redis_stores: Dict[str, "RedisIdempotencyStore"] = {}
_redis_lock = threading.Lock()


def get_idempotency_store() -> IdempotencyStore:
    if is_test_env():
        return _in_memory_store
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    # Reuse one client per URL instead of reconnecting (and pinging) on every webhook.
    with _redis_lock:
        store = _redis_stores.get(redis_url)
        if store is None or not store.is_available():
            store = RedisIdempotencyStore(redis_url)
            _redis_stores[redis_url] = store
    if not store.is_available():
        raise RuntimeError("Redis required outside test mode but unavailable")
    return store
