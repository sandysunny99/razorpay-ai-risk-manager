"""Threat intelligence service used by the payment pipeline.

Contract with the pipeline:
  * assess() is local-only and never raises; a broken store means "no matches", not a failed payment.
  * Matches become evidence (a risk factor and zombie input); the PolicyEngine still decides.
  * learn() feeds back only high-confidence outcomes: tokens the Zombie Card Saver said to revoke,
    and customer IPs on events from a trusted compromise assertion. Nothing is learned from
    ordinary risk blocks, which avoids feedback loops that would snowball false positives.
"""
import asyncio
import ipaddress
import logging
import os
from typing import List, Optional

from backend.threat_intel.feeds import live_feeds_enabled, load_seed, refresh_live_feeds, register_live_sources
from backend.threat_intel.store import IndicatorStore, ThreatMatch

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_S = int(os.getenv("NETVRIO_TI_REFRESH_S", str(6 * 3600)))


def _parse_ip(value) -> Optional[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    if not isinstance(value, str) or len(value) > 45:
        return None
    try:
        return ipaddress.ip_address(value.strip())
    except ValueError:
        return None


class ThreatIntelService:
    def __init__(self, store: Optional[IndicatorStore] = None):
        self.store = store or IndicatorStore()
        load_seed(self.store)
        register_live_sources(self.store)
        self._task: Optional[asyncio.Task] = None

    def assess(self, tenant_id: str, event_id: str, ip_address: Optional[str], token: Optional[str]) -> List[ThreatMatch]:
        matches: List[ThreatMatch] = []
        try:
            ip = _parse_ip(ip_address)
            if ip is not None:
                matches.extend(self.store.match_ip(tenant_id, ip))
            if token and token != "unknown":
                matches.extend(self.store.match_token(tenant_id, token))
            self.store.record(tenant_id, event_id, matches)
        except Exception as exc:  # noqa: BLE001
            logger.warning("threat intel assess failed: %s", type(exc).__name__)
            return []
        return matches

    def learn(self, tenant_id: str, *, token: Optional[str], ip_address: Optional[str],
              zombie_recommendation: Optional[str], compromised_source: bool) -> None:
        try:
            if token and token != "unknown" and zombie_recommendation == "REVOKE_TOKEN":
                self.store.revoke_token(tenant_id, token)
            ip = _parse_ip(ip_address)
            if ip is not None and compromised_source and ip.is_global:
                self.store.learn_ip(tenant_id, ip, "compromise_origin")
        except Exception as exc:  # noqa: BLE001
            logger.warning("threat intel learn failed: %s", type(exc).__name__)

    def status(self, tenant_id: str) -> dict:
        return {
            "live_feeds_enabled": live_feeds_enabled(),
            "sources": self.store.sources(),
            "lookups": self.store.lookups,
            "hits": self.store.hits,
            "learned": self.store.learned_counts(tenant_id),
        }

    def refresh(self) -> dict:
        if not live_feeds_enabled():
            return {}
        return refresh_live_feeds(self.store)

    # Background refresh (started from the app lifespan when live feeds are enabled).
    async def _loop(self) -> None:
        while True:
            await asyncio.to_thread(self.refresh)
            await asyncio.sleep(REFRESH_INTERVAL_S)

    def start_background_refresh(self) -> None:
        if live_feeds_enabled() and self._task is None:
            self._task = asyncio.get_running_loop().create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None


threat_intel = ThreatIntelService()
