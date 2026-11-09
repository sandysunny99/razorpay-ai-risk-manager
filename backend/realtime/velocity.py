"""Sliding-window behavioural counters computed from traffic the pipeline has actually accepted.

Replaces caller-supplied velocity with observed velocity: a customer's transactions in the last
hour, and how often a non-active (expired/replaced) card token was reused in the last 24 hours.
Keys are tenant-scoped; only opaque identifiers (customer ids, vault tokens) are stored.
"""
from collections import defaultdict, deque
import threading
import time
from typing import Deque, Dict, Optional, Tuple

VELOCITY_WINDOW_S = 3600
REUSE_WINDOW_S = 86400
MAX_KEYS = 50_000


class SlidingCounter:
    def __init__(self, window_seconds: int):
        self.window = window_seconds
        self._events: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, tenant_id: str, key: str, now: Optional[float] = None) -> int:
        """Record one occurrence and return the count inside the window (including this one)."""
        now = time.time() if now is None else now
        with self._lock:
            if len(self._events) > MAX_KEYS:
                self._events.clear()  # Bounded memory for a demo-grade in-process store.
            dq = self._events[(tenant_id, key)]
            dq.append(now)
            cutoff = now - self.window
            while dq and dq[0] < cutoff:
                dq.popleft()
            return len(dq)


class BehaviourTracker:
    def __init__(self):
        self.customer_velocity = SlidingCounter(VELOCITY_WINDOW_S)
        self.token_reuse = SlidingCounter(REUSE_WINDOW_S)

    def observe(self, tenant_id: str, customer_id: Optional[str], token: Optional[str], lifecycle: Optional[str]) -> dict:
        observed = {"velocity_1h": None, "recent_reuse_count": None}
        if customer_id and customer_id != "unknown":
            observed["velocity_1h"] = self.customer_velocity.hit(tenant_id, customer_id)
        if token and token != "unknown" and lifecycle in ("EXPIRED", "REPLACED"):
            # Uses of a dead credential; the first sighting is not yet a "reuse".
            observed["recent_reuse_count"] = self.token_reuse.hit(tenant_id, token) - 1
        return observed


behaviour_tracker = BehaviourTracker()
