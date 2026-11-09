"""Open threat feeds and their safe loaders.

Sources (all free to use for this purpose; check each provider's terms before production use):
  * Tor Project bulk exit list: anonymizing exit relays (not malicious by itself, so moderate confidence).
  * Spamhaus DROP (IPv4): netblocks hijacked or leased by professional spam/cybercrime operations.

Live download is opt-in (NETVRIO_TI_LIVE_FEEDS=true). Downloads are HTTPS-only, size-capped and
time-limited; parsing accepts only well-formed, globally routable networks; on any failure the
previous indicator set stays in place (fail-static) and the error is reported on /intel/status.
"""
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
    for state, _ in LIVE_FEEDS:
        state.enabled = live_feeds_enabled()
        store.register_source(state)


def fetch_feed(url: str, client=None) -> str:
    """HTTPS-only, size-capped download. `client` is injectable for tests."""
    if not url.startswith("https://"):
        raise ValueError("feed URL must be https")
    import httpx

    own_client = client is None
    client = client or httpx.Client(timeout=FEED_TIMEOUT_S, follow_redirects=False)
    try:
        with client.stream("GET", url, headers={"User-Agent": "netvrio-threat-intel/1.0"}) as resp:
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
    fetcher = fetcher or fetch_feed
    results: Dict[str, int] = {}
    for state, parser in LIVE_FEEDS:
        try:
            text = fetcher(state.url or "")
            nets = parse_public_networks(parser(text))
            if not nets:
                raise ValueError("feed parsed to zero indicators")
            results[state.name] = store.load_networks(state.name, nets)
        except Exception as exc:  # noqa: BLE001 — a broken feed must never break the pipeline
            logger.warning("threat feed %s refresh failed: %s", state.name, type(exc).__name__)
            store.mark_error(state.name, f"{type(exc).__name__}: {exc}")
            results[state.name] = -1
    return results
