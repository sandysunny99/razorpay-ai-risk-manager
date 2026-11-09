"""Tenant-scoped, thread-safe in-process pub/sub for pipeline outcomes.

Publishers may run on worker threads (sync route handlers, the generator's thread pool);
subscribers are asyncio queues owned by SSE connections. Delivery uses
``loop.call_soon_threadsafe`` so publishing never blocks the pipeline.
"""
import asyncio
from collections import defaultdict, deque
import itertools
import threading
import time
from typing import Any, Deque, Dict, List, Tuple

HISTORY_SIZE = 500
SUBSCRIBER_QUEUE_SIZE = 1000


class EventBus:
    def __init__(self, history_size: int = HISTORY_SIZE):
        self._lock = threading.Lock()
        self._history: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=history_size))
        self._subscribers: Dict[str, List[Tuple[asyncio.AbstractEventLoop, asyncio.Queue]]] = defaultdict(list)
        self._seq = itertools.count(1)

    def publish(self, tenant_id: str, event: Dict[str, Any]) -> dict:
        enriched = {**event, "seq": next(self._seq), "ts": int(time.time() * 1000), "tenant_id": tenant_id}
        with self._lock:
            self._history[tenant_id].append(enriched)
            subscribers = list(self._subscribers.get(tenant_id, []))
        for loop, queue in subscribers:
            try:
                loop.call_soon_threadsafe(self._offer, queue, enriched)
            except RuntimeError:
                pass  # Subscriber's loop already closed; it will be removed on unsubscribe.
        return enriched

    @staticmethod
    def _offer(queue: asyncio.Queue, event: dict) -> None:
        if queue.full():
            try:
                queue.get_nowait()  # Drop oldest for slow consumers rather than blocking publishers.
            except asyncio.QueueEmpty:
                pass
        queue.put_nowait(event)

    def subscribe(self, tenant_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=SUBSCRIBER_QUEUE_SIZE)
        with self._lock:
            self._subscribers[tenant_id].append((asyncio.get_running_loop(), queue))
        return queue

    def unsubscribe(self, tenant_id: str, queue: asyncio.Queue) -> None:
        with self._lock:
            self._subscribers[tenant_id] = [(lp, q) for lp, q in self._subscribers[tenant_id] if q is not queue]

    def recent(self, tenant_id: str, limit: int = 100) -> List[dict]:
        with self._lock:
            items = list(self._history.get(tenant_id, ()))
        return items[-limit:]

    def subscriber_count(self, tenant_id: str) -> int:
        with self._lock:
            return len(self._subscribers.get(tenant_id, []))

    def clear(self) -> None:
        with self._lock:
            self._history.clear()


event_bus = EventBus()
