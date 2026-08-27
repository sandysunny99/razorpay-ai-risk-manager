from abc import ABC, abstractmethod
import time
from typing import Any, Dict

import httpx


class BinProvider(ABC):
    @abstractmethod
    def lookup_bin(self, bin_number: str) -> Dict[str, Any]:
        """Lookup BIN metadata. bin_number must only be 6 to 8 digits."""
        pass

class MockBinProvider(BinProvider):
    """
    Deterministic offline BIN metadata provider.
    Provides standard bank/issuer and network card schemes.
    """
    IIN_REGISTRY = {
        "453201": {"scheme": "visa", "type": "credit", "brand": "traditional", "bank": "HDFC Bank", "country": "IN"},
        "411111": {"scheme": "visa", "type": "debit", "brand": "classic", "bank": "State Bank of India", "country": "IN"},
        "520000": {"scheme": "mastercard", "type": "credit", "brand": "world", "bank": "ICICI Bank", "country": "IN"},
        "542418": {"scheme": "mastercard", "type": "debit", "brand": "platinum", "bank": "Axis Bank", "country": "IN"},
        "370000": {"scheme": "amex", "type": "credit", "brand": "corporate", "bank": "American Express", "country": "US"},
        "608000": {"scheme": "rupay", "type": "debit", "brand": "platinum", "bank": "Bank of Baroda", "country": "IN"},
        "652150": {"scheme": "rupay", "type": "credit", "brand": "select", "bank": "Punjab National Bank", "country": "IN"},
    }

    def lookup_bin(self, bin_number: str) -> Dict[str, Any]:
        prefix_6 = str(bin_number)[:6] if bin_number else ""
        if prefix_6 in self.IIN_REGISTRY:
            data = self.IIN_REGISTRY[prefix_6].copy()
            data["cached"] = True
            data["provider"] = "MOCK_BINLIST"
            return data

        first_digit = prefix_6[:1] if prefix_6 else ""
        scheme = "visa" if first_digit == "4" else ("mastercard" if first_digit == "5" else ("rupay" if first_digit == "6" else "generic"))
        return {
            "scheme": scheme,
            "type": "credit",
            "brand": "standard",
            "bank": "Standard Chartered / Partner Bank",
            "country": "IN",
            "cached": True,
            "provider": "MOCK_BINLIST"
        }

class BinlistProvider(BinProvider):
    """
    Bounded Binlist.net HTTP provider with strict rate-limiting and in-memory TTL caching.
    Note: Binlist public limits are respected; cache duration is 24 hours.
    """
    BASE_URL = "https://lookup.binlist.net"

    def __init__(self, cache_ttl_seconds: int = 86400, timeout_seconds: float = 3.0, offline_mode: bool = False):
        self.cache_ttl = cache_ttl_seconds
        self.timeout = timeout_seconds
        self.offline_mode = offline_mode
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._fallback = MockBinProvider()
        self.last_call_timestamp: float = 0.0
        self.rate_limit_interval: float = 1.0

    def lookup_bin(self, bin_number: str) -> Dict[str, Any]:
        clean_bin = str(bin_number).replace(" ", "").replace("-", "")[:6]
        if len(clean_bin) < 6:
            return {"error": "Invalid BIN length (must be >= 6 digits)", "provider": "BINLIST", "status": "INVALID"}

        # 1. If known IIN in registry, return immediate deterministic metadata
        if clean_bin in MockBinProvider.IIN_REGISTRY:
            return self._fallback.lookup_bin(clean_bin)

        # 2. Check in-memory cache
        now = time.time()
        if clean_bin in self._cache:
            entry = self._cache[clean_bin]
            if now < entry["expiry"]:
                cached_data = entry["data"].copy()
                cached_data["cached"] = True
                cached_data["provider"] = "BINLIST_CACHE"
                return cached_data

        if self.offline_mode or (now - self.last_call_timestamp < self.rate_limit_interval):
            fallback = self._fallback.lookup_bin(clean_bin)
            fallback["provider"] = "BINLIST_OFFLINE_FALLBACK"
            return fallback

        # 3. Live Binlist API call
        try:
            self.last_call_timestamp = time.time()
            headers = {"Accept-Version": "3"}
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(f"{self.BASE_URL}/{clean_bin}", headers=headers)
                if res.status_code == 200:
                    raw = res.json()
                    parsed = {
                        "scheme": raw.get("scheme", "visa"),
                        "type": raw.get("type", "credit"),
                        "brand": raw.get("brand", "standard"),
                        "bank": raw.get("bank", {}).get("name", "Unknown Issuer"),
                        "country": raw.get("country", {}).get("alpha2", "IN"),
                        "cached": False,
                        "provider": "BINLIST_LIVE"
                    }
                    self._cache[clean_bin] = {"expiry": now + self.cache_ttl, "data": parsed}
                    return parsed
        except Exception:
            pass

        fallback = self._fallback.lookup_bin(clean_bin)
        fallback["provider"] = "BINLIST_OFFLINE_FALLBACK"
        return fallback

# Global provider instance
bin_provider = BinlistProvider()
