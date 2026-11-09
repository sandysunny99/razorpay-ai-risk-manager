from abc import ABC, abstractmethod
import os
import threading
from typing import Set

import redis


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
    def __init__(self):
        self._events: Set[str] = set()
        self._lock = threading.Lock()
    def _key(self, event_id: str, tenant_id: str) -> str:
        return f"{tenant_id}:{event_id}"
    def register_event(self, event_id: str, tenant_id: str) -> bool:
        key = self._key(event_id, tenant_id)
        with self._lock:
            if key in self._events:
                return False
            self._events.add(key)
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

def get_idempotency_store() -> IdempotencyStore:
    env = os.environ.get("NETVRIO_ENV", "test")
    if env == "test":
        global _in_memory_store
        if "_in_memory_store" not in globals():
            _in_memory_store = InMemoryIdempotencyStore()
        return _in_memory_store
    else:
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        store = RedisIdempotencyStore(redis_url)
        if not store.is_available():
            raise RuntimeError("Redis required in production but unavailable")
        return store
