"""Provider chain, call scope and budget for the advisory LLM.

NETVRIO_LLM_CHAIN       comma-separated fallback order (default: cloudflare,groq,gemini,nvidia,huggingface,grok).
                        Only providers whose credentials are present are called.
NETVRIO_LLM_SCOPE       "flagged" (default): only payments that are not plainly safe get an AI note.
                        "all": every payment (tests, or very low traffic).
NETVRIO_LLM_MAX_PER_MIN rolling budget of LLM calls per minute (default 20). Over budget the payment is
                        decided normally and simply carries no AI note.

The LLM is advisory only: none of these settings can change a decision.
"""
from collections import deque
import os
import threading
import time
from typing import Deque, Dict, List

from backend.llm.interfaces import RiskLLMProvider
from backend.llm.providers import (
    CloudflareProvider,
    GeminiProvider,
    GrokProvider,
    GroqProvider,
    HuggingFaceRouterProvider,
    NvidiaProvider,
)

DEFAULT_CHAIN = "cloudflare,groq,gemini,nvidia,huggingface,grok"
REGISTRY = {
    "cloudflare": CloudflareProvider,
    "groq": GroqProvider,
    "gemini": GeminiProvider,
    "nvidia": NvidiaProvider,
    "huggingface": HuggingFaceRouterProvider,  # current router; legacy endpoint is retired
    "grok": GrokProvider,
}


def chain_names() -> List[str]:
    names = [n.strip().lower() for n in os.getenv("NETVRIO_LLM_CHAIN", DEFAULT_CHAIN).split(",")]
    return [n for n in dict.fromkeys(names) if n in REGISTRY]


def build_all() -> List[RiskLLMProvider]:
    """Every provider in the configured order, configured or not (for health display)."""
    return [REGISTRY[n]() for n in chain_names()]


def is_configured(provider: RiskLLMProvider) -> bool:
    if isinstance(provider, CloudflareProvider):
        return bool(provider.token and provider.account_id)
    return bool(getattr(provider, "api_key", None))


def build_active() -> List[RiskLLMProvider]:
    """Providers the router should actually call: configured ones, in chain order."""
    return [p for p in build_all() if is_configured(p)]


def scope_all() -> bool:
    return os.getenv("NETVRIO_LLM_SCOPE", "flagged").lower() == "all"


class CallBudget:
    def __init__(self):
        self._lock = threading.Lock()
        self._calls: Deque[float] = deque()

    def limit(self) -> int:
        try:
            return max(0, int(os.getenv("NETVRIO_LLM_MAX_PER_MIN", "20")))
        except ValueError:
            return 20

    def take(self) -> bool:
        now = time.monotonic()
        with self._lock:
            while self._calls and now - self._calls[0] > 60:
                self._calls.popleft()
            if len(self._calls) >= self.limit():
                return False
            self._calls.append(now)
            return True

    def used(self) -> Dict[str, int]:
        now = time.monotonic()
        with self._lock:
            return {"used_last_minute": sum(1 for t in self._calls if now - t <= 60), "limit_per_minute": self.limit()}


budget = CallBudget()
