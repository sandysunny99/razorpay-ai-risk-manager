"""Live synthetic traffic generator.

Produces a continuous, realistic stream of *signed* payment webhooks for a tenant and runs every
one of them through the real protected pipeline (``run_pipeline``) — nothing is pre-scored. A
configurable share of the traffic is adversarial (forged signatures, replays, duplicate
deliveries, cross-tenant injection, raw PAN submissions) so the security controls can be watched
working in real time.

All data is synthetic. Customers and tokens are drawn from a small pool so that behavioural
signals (velocity, dead-token reuse) emerge naturally from the traffic itself.
"""
import asyncio
from dataclasses import dataclass, field
import hashlib
import hmac
import json
import os
import random
import time
from typing import Callable, Dict, List, Optional, Tuple
import uuid

from fastapi import HTTPException

# Synthetic population ------------------------------------------------------------------------
# The pool must be large relative to the event rate: at 2 events/s, 5,000 customers average about
# 1.4 payments per hour each, like real shoppers. (A 120-customer pool made everyone look like a bot
# under the 1-hour velocity window and flooded the review queue.)
_CUSTOMERS = [f"cust_{i:05d}" for i in range(1, 5001)]
_BURST_CUSTOMERS = [f"cust_bot_{i}" for i in range(1, 5)]  # a few bot-like customers that burst
_ACTIVE_TOKENS = [f"tok_live_{i:04d}" for i in range(1, 201)]
_EXPIRED_TOKENS = [f"tok_expired_{i:03d}" for i in range(1, 9)]  # small pool => reuse accumulates
_METHODS = ["card", "card", "card", "upi", "upi", "netbanking", "wallet"]
_CHANNELS = ["web", "android", "ios", "pos"]

# Customer IPs come from RFC 6598 shared address space (not anyone's real address); hostile IPs
# come from the RFC 5737 ranges listed in the synthetic threat feed.
_THREAT_NETS = [("192.0.2", 0, 127), ("198.51.100", 0, 255), ("203.0.113", 128, 255)]

def _luhn_check_digit(body: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(body)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - total % 10) % 10)


def synthetic_pan(token: str) -> str:
    """Deterministic, Luhn-valid number in the non-issuable 999990 range, one per synthetic token.
    Only used to derive fingerprints for the exposure-monitoring drill; never sent in payloads."""
    body = "999990" + str(int(hashlib.sha256(token.encode()).hexdigest(), 16))[-9:]
    return body + _luhn_check_digit(body)


def synthetic_fingerprint(token: str) -> Optional[str]:
    secret_hex = os.getenv("FINGERPRINT_HMAC_SECRET")
    if not secret_hex:
        return None
    return "fp_" + hmac.new(bytes.fromhex(secret_hex), synthetic_pan(token).encode(), hashlib.sha256).hexdigest()[:16]


ATTACKS = ("forged_signature", "replay_stale", "duplicate_delivery", "cross_tenant", "raw_pan")


@dataclass
class GeneratorConfig:
    rate_per_sec: float = 2.0      # events per second
    attack_ratio: float = 0.12     # share of adversarial traffic
    risky_ratio: float = 0.20      # share of legitimate-but-risky traffic (high value, bursts, zombies)


@dataclass
class GeneratorState:
    running: bool = False
    emitted: int = 0
    started_at: Optional[float] = None
    by_scenario: Dict[str, int] = field(default_factory=dict)


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


class TrafficGenerator:
    def __init__(
        self,
        tenant_id: str,
        secret_provider: Callable[[], str],
        processor: Callable[..., dict],
        rng: Optional[random.Random] = None,
    ):
        self.tenant_id = tenant_id
        self._secret_provider = secret_provider
        self._process = processor
        self._rng = rng or random.Random()
        self.config = GeneratorConfig()
        self.state = GeneratorState()
        self._task: Optional[asyncio.Task] = None
        self._last_valid: Optional[Tuple[bytes, str]] = None

    # ── payload construction ────────────────────────────────────────────────────────────────
    def _base(self, data: dict, token: Optional[str] = None, merchant_id: Optional[str] = None,
              timestamp: Optional[int] = None) -> dict:
        payload = {
            "event_id": f"evt_live_{uuid.uuid4().hex[:16]}",
            "timestamp": int(time.time()) if timestamp is None else timestamp,
            "merchant_id": merchant_id or self.tenant_id,
            "event_type": "payment.authorized",
            "data": {
                "currency": "INR",
                "ip_address": self._customer_ip(),
                "method": self._rng.choice(_METHODS),
                "channel": self._rng.choice(_CHANNELS),
                **data,
            },
        }
        if token:
            payload["token"] = token
            if payload["data"].get("method") == "card":
                fp = synthetic_fingerprint(token)
                if fp:
                    payload["fingerprint"] = fp
        return payload

    def _customer_ip(self) -> str:
        return f"100.{self._rng.randint(64, 127)}.{self._rng.randint(0, 255)}.{self._rng.randint(1, 254)}"

    def _threat_ip(self) -> str:
        prefix, lo, hi = self._rng.choice(_THREAT_NETS)
        return f"{prefix}.{self._rng.randint(max(lo, 1), min(hi, 254))}"

    def _legit(self) -> Tuple[str, dict]:
        r = self._rng.random()
        risky = r < self.config.risky_ratio
        if not risky:
            amount = round(min(9500.0, self._rng.lognormvariate(6.2, 1.0)), 2)  # median ≈ ₹490
            return "normal", self._base(
                {"amount": amount, "customer_id": self._rng.choice(_CUSTOMERS)}, self._rng.choice(_ACTIVE_TOKENS)
            )
        kind = self._rng.choices(
            ["high_value", "very_high_value", "velocity_burst", "zombie_reuse", "compromised_token", "threat_ip"],
            weights=[26, 10, 22, 22, 6, 14],
        )[0]
        if kind == "threat_ip":
            data = {"amount": round(self._rng.uniform(300, 9000), 2), "customer_id": self._rng.choice(_CUSTOMERS),
                    "ip_address": self._threat_ip()}
            return kind, self._base(data, self._rng.choice(_ACTIVE_TOKENS))
        if kind == "high_value":
            data = {"amount": round(self._rng.uniform(10500, 60000), 2), "customer_id": self._rng.choice(_CUSTOMERS)}
            return kind, self._base(data, self._rng.choice(_ACTIVE_TOKENS))
        if kind == "very_high_value":
            data = {"amount": round(self._rng.uniform(100500, 250000), 2), "customer_id": self._rng.choice(_CUSTOMERS)}
            return kind, self._base(data, self._rng.choice(_ACTIVE_TOKENS))
        if kind == "velocity_burst":
            data = {"amount": round(self._rng.uniform(200, 2500), 2), "customer_id": self._rng.choice(_BURST_CUSTOMERS)}
            return kind, self._base(data, self._rng.choice(_ACTIVE_TOKENS))
        if kind == "zombie_reuse":
            data = {"amount": round(self._rng.uniform(99, 1999), 2), "customer_id": self._rng.choice(_CUSTOMERS),
                    "card_lifecycle": "EXPIRED"}
            return kind, self._base(data, self._rng.choice(_EXPIRED_TOKENS))
        data = {"amount": round(self._rng.uniform(500, 15000), 2), "customer_id": self._rng.choice(_CUSTOMERS),
                "trusted_compromise_assertion": True}
        return "compromised_token", self._base(data, self._rng.choice(_EXPIRED_TOKENS))

    def build_event(self, attack: Optional[str] = None) -> Tuple[str, bytes, str, str]:
        """Return (scenario, raw_body, signature, tenant_header)."""
        secret = self._secret_provider()
        if attack is None:
            scenario, payload = self._legit()
            body = json.dumps(payload, separators=(",", ":")).encode()
            sig = _sign(secret, body)
            self._last_valid = (body, sig)
            return scenario, body, sig, self.tenant_id

        if attack == "duplicate_delivery" and self._last_valid:
            body, sig = self._last_valid
            return attack, body, sig, self.tenant_id

        amount = round(self._rng.uniform(100, 5000), 2)
        if attack == "forged_signature":
            body = json.dumps(self._base({"amount": amount}), separators=(",", ":")).encode()
            return attack, body, "0" * 64, self.tenant_id
        if attack == "replay_stale":
            payload = self._base({"amount": amount}, timestamp=int(time.time()) - self._rng.randint(600, 7200))
            body = json.dumps(payload, separators=(",", ":")).encode()
            return attack, body, _sign(secret, body), self.tenant_id
        if attack == "cross_tenant":
            payload = self._base({"amount": amount}, merchant_id="tenant_victim_999")
            body = json.dumps(payload, separators=(",", ":")).encode()
            return attack, body, _sign(secret, body), self.tenant_id
        # raw_pan (also the fallback for duplicate_delivery before any valid event exists)
        payload = self._base({"amount": amount})
        payload["card_pan"] = "4111" + "1111" * 3  # Public test PAN — must be rejected at ingress.
        body = json.dumps(payload, separators=(",", ":")).encode()
        return "raw_pan", body, _sign(secret, body), self.tenant_id

    # ── execution ───────────────────────────────────────────────────────────────────────────
    def emit_once(self, attack: Optional[str] = None) -> str:
        """Build one event and run it synchronously through the real pipeline."""
        if attack is None and self._rng.random() < self.config.attack_ratio:
            attack = self._rng.choice(ATTACKS)
        scenario, body, sig, tenant = self.build_event(attack)
        try:
            self._process(body, sig, tenant, self._secret_provider(), f"corr_{uuid.uuid4()}",
                          source="generator", scenario=scenario)
        except HTTPException:
            pass  # Rejections are expected for attacks and are already published to the bus.
        self.state.emitted += 1
        self.state.by_scenario[scenario] = self.state.by_scenario.get(scenario, 0) + 1
        return scenario

    async def _loop(self) -> None:
        while self.state.running:
            started = time.perf_counter()
            try:
                await asyncio.to_thread(self.emit_once)
            except Exception:  # noqa: BLE001 — a bad event must never kill the live stream
                pass
            interval = 1.0 / max(0.1, self.config.rate_per_sec)
            # Poisson-ish arrivals look like real traffic rather than a metronome.
            delay = self._rng.expovariate(1.0 / interval) - (time.perf_counter() - started)
            await asyncio.sleep(max(0.01, min(delay, interval * 4)))

    def start(self) -> None:
        if self.state.running:
            return
        self.state.running = True
        self.state.started_at = time.time()
        self._task = asyncio.get_running_loop().create_task(self._loop())

    async def stop(self) -> None:
        self.state.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None

    def configure(self, rate_per_sec: Optional[float] = None, attack_ratio: Optional[float] = None,
                  risky_ratio: Optional[float] = None) -> None:
        if rate_per_sec is not None:
            self.config.rate_per_sec = max(0.2, min(20.0, float(rate_per_sec)))
        if attack_ratio is not None:
            self.config.attack_ratio = max(0.0, min(0.9, float(attack_ratio)))
        if risky_ratio is not None:
            self.config.risky_ratio = max(0.0, min(0.9, float(risky_ratio)))

    def status(self) -> dict:
        return {
            "running": self.state.running,
            "tenant_id": self.tenant_id,
            "rate_per_sec": self.config.rate_per_sec,
            "attack_ratio": self.config.attack_ratio,
            "risky_ratio": self.config.risky_ratio,
            "emitted": self.state.emitted,
            "started_at": self.state.started_at,
            "by_scenario": dict(self.state.by_scenario),
        }


_generators: Dict[str, TrafficGenerator] = {}


def get_generator(tenant_id: str) -> TrafficGenerator:
    if tenant_id not in _generators:
        from backend.api.dependencies import get_webhook_secret
        from backend.api.routes.webhooks import process_and_publish

        _generators[tenant_id] = TrafficGenerator(tenant_id, get_webhook_secret, process_and_publish)
    return _generators[tenant_id]


def all_generators() -> List[TrafficGenerator]:
    return list(_generators.values())
