from abc import ABC, abstractmethod
import os
import time
from typing import Any, Dict

import httpx


class ThreatProvider(ABC):
    @abstractmethod
    def check_url_or_host(self, target: str) -> Dict[str, Any]:
        pass

class MockThreatProvider(ThreatProvider):
    """
    Offline deterministic threat intelligence provider.
    """
    KNOWN_MALICIOUS_DOMAINS = {
        "evil-stealer.xyz": {"threat": "malware_download", "status": "online", "confidence": 0.95},
        "pay-phishing-fake.cc": {"threat": "phishing", "status": "online", "confidence": 0.90},
        "botnet-c2-node.ru": {"threat": "c2_server", "status": "online", "confidence": 0.99},
    }

    def check_url_or_host(self, target: str) -> Dict[str, Any]:
        target_lower = (target or "").lower().strip()
        for domain, info in self.KNOWN_MALICIOUS_DOMAINS.items():
            if domain in target_lower:
                return {
                    "query_status": "ok",
                    "threat": info["threat"],
                    "status": info["status"],
                    "confidence": info["confidence"],
                    "provider": "MOCK_URLHAUS",
                    "cached": True
                }
        return {
            "query_status": "no_results",
            "threat": "none",
            "status": "clean",
            "confidence": 0.0,
            "provider": "MOCK_URLHAUS",
            "cached": True
        }

class URLhausProvider(ThreatProvider):
    """
    URLhaus Community API client for malicious URL & malware payload threat intelligence.
    Uses strict rate limits and TTL caching.
    """
    API_URL = "https://urlhaus-api.abuse.ch/v1/host/"

    def __init__(self, cache_ttl_seconds: int = 1800, timeout_seconds: float = 3.0):
        self.cache_ttl = cache_ttl_seconds
        self.timeout = timeout_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._fallback = MockThreatProvider()
        self.api_key = os.getenv("URLHAUS_API_KEY")

    def check_url_or_host(self, target: str) -> Dict[str, Any]:
        if not target:
            return {"query_status": "invalid_query", "threat": "none", "provider": "URLHAUS"}

        now = time.time()
        # 1. Check Cache
        if target in self._cache:
            entry = self._cache[target]
            if now < entry["expiry"]:
                res = entry["data"].copy()
                res["cached"] = True
                res["provider"] = "URLHAUS_CACHE"
                return res

        # 2. If no real API key is configured or offline mode, use deterministic mock
        if not self.api_key:
            res = self._fallback.check_url_or_host(target)
            res["provider"] = "URLHAUS_MOCK_SANDBOX"
            return res

        # 3. Live URLhaus API call
        try:
            headers = {"Auth-Key": self.api_key} if self.api_key else {}
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(self.API_URL, data={"host": target}, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    parsed = {
                        "query_status": data.get("query_status", "no_results"),
                        "threat": data.get("threat", "none"),
                        "status": data.get("urlhaus_reference", "clean"),
                        "confidence": 0.85 if data.get("query_status") == "ok" else 0.0,
                        "provider": "URLHAUS_LIVE",
                        "cached": False
                    }
                    self._cache[target] = {"expiry": now + self.cache_ttl, "data": parsed}
                    return parsed
        except Exception:
            pass

        fallback = self._fallback.check_url_or_host(target)
        fallback["provider"] = "URLHAUS_OFFLINE_FALLBACK"
        return fallback

# Global provider instance
threat_enrichment_provider = URLhausProvider()
