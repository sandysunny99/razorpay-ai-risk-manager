"""Open threat feeds and their safe loaders.

Sources (check each provider's terms before production use):
  * Tor Project bulk exit list: anonymizing exit relays (not malicious by itself, so moderate confidence).
  * Spamhaus DROP (IPv4): netblocks hijacked or leased by professional spam/cybercrime operations.
  * abuse.ch Feodo Tracker: botnet C2 servers of banking trojans (no key).
  * abuse.ch ThreatFox: recent IOCs; only ip:port entries are used (needs ABUSE_CH_AUTH_KEY).
  * AlienVault OTX: IPv4 indicators from the pulses your account subscribes to (needs OTX_API_KEY).
Keyed sources are active only when their key is set. Keys are sent only to their own provider.

Live download is opt-in (NETVRIO_TI_LIVE_FEEDS=true). Downloads are HTTPS-only, size-capped and
time-limited; parsing accepts only well-formed, globally routable networks; on any failure the
previous indicator set stays in place (fail-static) and the error is reported on /intel/status.
"""
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from backend.threat_intel.store import IndicatorStore, SourceState, parse_public_networks

logger = logging.getLogger(__name__)

MAX_FEED_BYTES = 5 * 1024 * 1024
FEED_TIMEOUT_S = 10.0
SEED_PATH = Path(__file__).with_name("seed_indicators.json")


def _parse_lines(text: str) -> List[str]:
    return [line for line in text.splitlines() if line and not line.lstrip().startswith(("#", ";"))]


def _parse_spamhaus(text: str) -> List[str]:
    """Spamhaus publishes NDJSON (drop_v4.json) with a "cidr" key; the legacy .txt is 'CIDR ; SBL'."""
    out: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("{"):
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if isinstance(obj, dict) and isinstance(obj.get("cidr"), str):
                out.append(obj["cidr"])
        elif not line.startswith(";"):
            out.append(line)
    return out


def _parse_feodo(text: str) -> List[str]:
    data = json.loads(text)
    return [str(d["ip_address"]) for d in data if isinstance(d, dict) and d.get("ip_address")] if isinstance(data, list) else []


def _parse_threatfox(text: str) -> List[str]:
    data = json.loads(text)
    rows = data.get("data") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return []
    return [str(r["ioc"]).rsplit(":", 1)[0] for r in rows
            if isinstance(r, dict) and r.get("ioc_type") == "ip:port" and r.get("ioc")]


def _parse_otx(text: str) -> List[str]:
    """IPv4 indicators from subscribed pulses (the bulk export endpoint is too slow to be usable)."""
    data = json.loads(text)
    pulses = data.get("results") if isinstance(data, dict) else None
    if not isinstance(pulses, list):
        return []
    return [str(i.get("indicator", "")) for p in pulses if isinstance(p, dict)
            for i in (p.get("indicators") or []) if isinstance(i, dict) and i.get("type") == "IPv4"]


@dataclass
class FeedSpec:
    state: SourceState
    parser: Callable[[str], List[str]]
    method: str = "GET"
    auth_header: Optional[str] = None   # header name carrying the key
    key_env: Optional[str] = None       # environment variable holding the key; None = no key needed
    body: Optional[dict] = None

    def active(self) -> bool:
        return self.key_env is None or bool(os.getenv(self.key_env))

    def headers(self) -> Dict[str, str]:
        if self.auth_header and self.key_env and os.getenv(self.key_env):
            return {self.auth_header: os.environ[self.key_env]}
        return {}


LIVE_FEEDS: List[Tuple[SourceState, Callable[[str], List[str]]]] = [
    (
        SourceState(
            name="tor-exit-nodes",
            category="anonymizer",
            confidence=0.6,
            url="https://check.torproject.org/torbulkexitlist",
            license="Tor Project, public list",
        ),
        _parse_lines,
    ),
    (
        SourceState(
            name="spamhaus-drop",
            category="hijacked_netblock",
            confidence=0.95,
            url="https://www.spamhaus.org/drop/drop_v4.json",
            license="Spamhaus DROP, free for non-commercial / limited use",
        ),
        _parse_spamhaus,
    ),
]

FEEDS: List[FeedSpec] = [FeedSpec(state, parser) for state, parser in LIVE_FEEDS] + [
    FeedSpec(
        SourceState(name="abusech-feodo", category="botnet_c2", confidence=0.9,
                    url="https://feodotracker.abuse.ch/downloads/ipblocklist.json",
                    license="abuse.ch Feodo Tracker, CC0"),
        _parse_feodo,
    ),
    FeedSpec(
        SourceState(name="abusech-threatfox", category="botnet_c2", confidence=0.8,
                    url="https://threatfox-api.abuse.ch/api/v1/",
                    license="abuse.ch ThreatFox, CC0 (Auth-Key required)"),
        _parse_threatfox, method="POST", auth_header="Auth-Key", key_env="ABUSE_CH_AUTH_KEY",
        body={"query": "get_iocs", "days": 3},
    ),
    FeedSpec(
        SourceState(name="alienvault-otx", category="reported_malicious", confidence=0.7,
                    url="https://otx.alienvault.com/api/v1/pulses/subscribed?limit=50&page=1",
                    license="AlienVault OTX (subscribed pulses)"),
        _parse_otx, auth_header="X-OTX-API-KEY", key_env="OTX_API_KEY",
    ),
]


def load_seed(store: IndicatorStore) -> int:
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    store.register_source(
        SourceState(name=data["source"], category="mixed", confidence=0.8, license=data.get("license", ""))
    )
    entries = data.get("indicators", [])
    nets = parse_public_networks(e["cidr"] for e in entries)
    per_network: Dict[str, Tuple[str, float]] = {}
    for e in entries:
        try:
            key = str(parse_public_networks([e["cidr"]])[0])
        except IndexError:
            continue
        per_network[key] = (str(e.get("category", "unknown")), float(e.get("confidence", 0.5)))
    return store.load_networks(data["source"], nets, per_network)


def live_feeds_enabled() -> bool:
    return os.getenv("NETVRIO_TI_LIVE_FEEDS", "false").lower() == "true"


def register_live_sources(store: IndicatorStore) -> None:
    for spec in FEEDS:
        spec.state.enabled = live_feeds_enabled() and spec.active()
        if spec.key_env is None or spec.active():
            store.register_source(spec.state)


def fetch_feed(url: str, client=None, method: str = "GET", headers: Optional[Dict[str, str]] = None,
               json_body: Optional[dict] = None) -> str:
    """HTTPS-only, size-capped download. `client` is injectable for tests."""
    if not url.startswith("https://"):
        raise ValueError("feed URL must be https")
    import httpx

    own_client = client is None
    client = client or httpx.Client(timeout=FEED_TIMEOUT_S, follow_redirects=False)
    try:
        req_headers = {"User-Agent": "netvrio-threat-intel/1.0", **(headers or {})}
        with client.stream(method, url, headers=req_headers, json=json_body) as resp:
            resp.raise_for_status()
            chunks, size = [], 0
            for chunk in resp.iter_bytes():
                size += len(chunk)
                if size > MAX_FEED_BYTES:
                    raise ValueError("feed exceeds size cap")
                chunks.append(chunk)
        return b"".join(chunks).decode("utf-8", errors="replace")
    finally:
        if own_client:
            client.close()


def refresh_live_feeds(store: IndicatorStore, fetcher: Optional[Callable[[str], str]] = None) -> Dict[str, int]:
    """Download and swap in each live feed. Failures keep the previous data (fail-static)."""
    results: Dict[str, int] = {}
    for spec in FEEDS:
        if not spec.active():
            continue
        state, parser = spec.state, spec.parser
        try:
            if fetcher is not None:  # tests inject a url -> text function
                text = fetcher(state.url or "")
            else:
                text = fetch_feed(state.url or "", method=spec.method, headers=spec.headers(), json_body=spec.body)
            nets = parse_public_networks(parser(text))
            if not nets:
                raise ValueError("feed parsed to zero indicators")
            results[state.name] = store.load_networks(state.name, nets)
        except Exception as exc:  # noqa: BLE001 — a broken feed must never break the pipeline
            logger.warning("threat feed %s refresh failed: %s", state.name, type(exc).__name__)
            store.mark_error(state.name, f"{type(exc).__name__}: {exc}")
            results[state.name] = -1
    return results
