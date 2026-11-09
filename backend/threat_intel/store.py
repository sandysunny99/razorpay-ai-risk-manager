"""Thread-safe local indicator store.

Lookups never leave the process: feeds are loaded in the background and the pipeline only does
in-memory set/prefix checks, so threat intel adds microseconds, not network round-trips, and no
customer data is sent to third parties.
"""
from collections import deque
from dataclasses import dataclass, field
import ipaddress
import threading
import time
from typing import Deque, Dict, Iterable, List, Optional, Set, Tuple

IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network
IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address

MAX_NETWORKS_PER_SOURCE = 250_000
LEARNED_TTL_S = 24 * 3600


@dataclass(frozen=True)
class ThreatMatch:
    indicator_type: str      # "ip" | "token"
    indicator: str           # display-safe form (masked IP, token prefix)
    source: str
    category: str
    confidence: float

    def to_dict(self) -> dict:
        return {
            "indicator_type": self.indicator_type,
            "indicator": self.indicator,
            "source": self.source,
            "category": self.category,
            "confidence": self.confidence,
        }


@dataclass
class SourceState:
    name: str
    category: str
    confidence: float
    url: Optional[str] = None
    license: str = ""
    enabled: bool = True
    indicators: int = 0
    last_refresh: Optional[float] = None
    last_error: Optional[str] = None
    # Prefix length -> set of network addresses (as ints) for O(#prefix lengths) lookups.
    v4: Dict[int, Set[int]] = field(default_factory=dict)
    v6: Dict[int, Set[int]] = field(default_factory=dict)
    # Per-network overrides (seed feeds carry their own category/confidence per entry).
    meta: Dict[Tuple[int, int, int], Tuple[str, float]] = field(default_factory=dict)

    def public(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "confidence": self.confidence,
            "url": self.url,
            "license": self.license,
            "enabled": self.enabled,
            "indicators": self.indicators,
            "last_refresh": self.last_refresh,
            "last_error": self.last_error,
        }


def mask_ip(ip: IPAddress) -> str:
    """Display-safe IP: keep the network, drop the host part (IPs can be personal data)."""
    if ip.version == 4:
        return str(ipaddress.ip_network(f"{ip}/24", strict=False).network_address) + "/24"
    return str(ipaddress.ip_network(f"{ip}/48", strict=False).network_address) + "/48"


def parse_public_networks(entries: Iterable[str]) -> List[IPNetwork]:
    """Strictly parse IPs/CIDRs, dropping anything that is not globally routable.

    Feeds such as bogon lists include private ranges; letting those through would flag internal
    traffic, so only global networks are kept. Documentation ranges (RFC 5737) are allowed so the
    synthetic seed feed works.
    """
    doc_ranges = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]
    nets: List[IPNetwork] = []
    for raw in entries:
        token = raw.strip().split(";")[0].split("#")[0].strip()
        if not token:
            continue
        try:
            net = ipaddress.ip_network(token, strict=False)
        except ValueError:
            continue
        is_doc = any(net.subnet_of(d) for d in doc_ranges if d.version == net.version)
        if not (net.is_global or is_doc):
            continue
        if net.prefixlen < (8 if net.version == 4 else 19):
            continue  # Refuse absurdly broad entries that would flag huge parts of the internet.
        nets.append(net)
        if len(nets) >= MAX_NETWORKS_PER_SOURCE:
            break
    return nets


class IndicatorStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._sources: Dict[str, SourceState] = {}
        self._revoked_tokens: Dict[Tuple[str, str], float] = {}       # (tenant, token) -> expiry
        self._learned_ips: Dict[Tuple[str, int], Tuple[str, float]] = {}  # (tenant, ip int) -> (category, expiry)
        self._matches: Dict[str, Deque[dict]] = {}
        self.lookups = 0
        self.hits = 0

    # ── feeds ───────────────────────────────────────────────────────────────────────────────
    def register_source(self, state: SourceState) -> None:
        with self._lock:
            self._sources.setdefault(state.name, state)

    def load_networks(self, source: str, networks: List[IPNetwork],
                      per_network: Optional[Dict[str, Tuple[str, float]]] = None) -> int:
        v4: Dict[int, Set[int]] = {}
        v6: Dict[int, Set[int]] = {}
        meta: Dict[Tuple[int, int, int], Tuple[str, float]] = {}
        for net in networks:
            bucket = v4 if net.version == 4 else v6
            bucket.setdefault(net.prefixlen, set()).add(int(net.network_address))
            if per_network and str(net) in per_network:
                meta[(net.version, net.prefixlen, int(net.network_address))] = per_network[str(net)]
        with self._lock:
            st = self._sources[source]
            st.v4, st.v6, st.meta = v4, v6, meta
            st.indicators = len(networks)
            st.last_refresh = time.time()
            st.last_error = None
        return len(networks)

    def mark_error(self, source: str, error: str) -> None:
        with self._lock:
            if source in self._sources:
                self._sources[source].last_error = error[:200]

    def sources(self) -> List[dict]:
        with self._lock:
            return [s.public() for s in self._sources.values()]

    # ── lookups ─────────────────────────────────────────────────────────────────────────────
    def match_ip(self, tenant_id: str, ip: IPAddress) -> List[ThreatMatch]:
        ip_int = int(ip)
        bits = 32 if ip.version == 4 else 128
        found: List[ThreatMatch] = []
        now = time.time()
        with self._lock:
            for st in self._sources.values():
                if not st.enabled:
                    continue
                table = st.v4 if ip.version == 4 else st.v6
                for prefix, nets in table.items():
                    net_int = (ip_int >> (bits - prefix)) << (bits - prefix) if prefix else 0
                    if net_int in nets:
                        category, conf = st.meta.get((ip.version, prefix, net_int), (st.category, st.confidence))
                        found.append(ThreatMatch("ip", mask_ip(ip), st.name, category, conf))
                        break
            learned = self._learned_ips.get((tenant_id, ip_int))
            if learned and learned[1] > now:
                found.append(ThreatMatch("ip", mask_ip(ip), "netvrio-learned", learned[0], 0.7))
        return found

    def match_token(self, tenant_id: str, token: str) -> List[ThreatMatch]:
        with self._lock:
            expiry = self._revoked_tokens.get((tenant_id, token))
        if expiry and expiry > time.time():
            return [ThreatMatch("token", token[:8] + "…", "netvrio-learned", "revoked_token", 1.0)]
        return []

    # ── learning ────────────────────────────────────────────────────────────────────────────
    def revoke_token(self, tenant_id: str, token: str, ttl: int = 30 * 24 * 3600) -> None:
        with self._lock:
            self._revoked_tokens[(tenant_id, token)] = time.time() + ttl

    def learn_ip(self, tenant_id: str, ip: IPAddress, category: str, ttl: int = LEARNED_TTL_S) -> None:
        with self._lock:
            if len(self._learned_ips) > 100_000:
                self._learned_ips.clear()
            self._learned_ips[(tenant_id, int(ip))] = (category, time.time() + ttl)

    def learned_counts(self, tenant_id: str) -> dict:
        now = time.time()
        with self._lock:
            return {
                "revoked_tokens": sum(1 for (t, _), exp in self._revoked_tokens.items() if t == tenant_id and exp > now),
                "watched_ips": sum(1 for (t, _), (_, exp) in self._learned_ips.items() if t == tenant_id and exp > now),
            }

    # ── match log ───────────────────────────────────────────────────────────────────────────
    def record(self, tenant_id: str, event_id: str, matches: List[ThreatMatch]) -> None:
        with self._lock:
            self.lookups += 1
            if not matches:
                return
            self.hits += 1
            log = self._matches.setdefault(tenant_id, deque(maxlen=200))
            log.append({"event_id": event_id, "ts": int(time.time() * 1000), "matches": [m.to_dict() for m in matches]})

    def recent_matches(self, tenant_id: str, limit: int = 50) -> List[dict]:
        with self._lock:
            return list(self._matches.get(tenant_id, ()))[-limit:][::-1]
