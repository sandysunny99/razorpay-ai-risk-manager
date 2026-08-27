"""
backend/app/enrichment/external_apis.py
========================================
Phase 2 — Free API Integration Layer

All integrations follow the STRICT graceful degradation principle:
  - If the API key is not set → return None / 0.0 immediately (no network call)
  - If the API is unreachable or times out → return None / 0.0 (never raise)
  - If the response is malformed → return None / 0.0

This ensures the demo works with ZERO configuration and all 5 golden scenarios
remain functional even if every API key is missing.

APIs:
  1. ip-api.com      — real geo-deviation (no auth, 45 req/min free)
  2. HIBP v3         — dark web breach correlation (env: HIBP_API_KEY)
  3. AbuseIPDB       — IP reputation scoring (env: ABUSEIPDB_API_KEY)
"""
import logging
import math
from typing import Optional

logger = logging.getLogger("external_apis")

# ─────────────────────────────────────────────────────────────────────────────
# Lazy httpx import — only loaded when an actual API call is made
# ─────────────────────────────────────────────────────────────────────────────
_httpx_available = False
try:
    import httpx  # noqa: F401
    _httpx_available = True
except ImportError:
    logger.warning("httpx not installed — external API integrations will be skipped.")


def _is_private_ip(ip: str) -> bool:
    """Return True for RFC-1918 / loopback / APIPA addresses (skip geo lookup)."""
    private_prefixes = ("10.", "192.168.", "127.", "169.254.", "172.16.", "172.17.",
                        "172.18.", "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
                        "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                        "172.30.", "172.31.", "::1", "fc", "fd")
    return any(ip.startswith(p) for p in private_prefixes)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two coordinate pairs (km)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ─────────────────────────────────────────────────────────────────────────────
# 1. ip-api.com — Real Geo-Deviation (no auth required)
# ─────────────────────────────────────────────────────────────────────────────

async def get_real_geo_for_ip(ip: str) -> Optional[dict]:
    """
    Fetch real geolocation for a public IP via ip-api.com.
    Free tier: 45 requests/minute, no authentication required.

    Returns dict with keys: lat, lon, country, city, isp
    Returns None on private IP, missing httpx, or any failure.
    """
    if not ip or not _httpx_available:
        return None
    if _is_private_ip(ip):
        return None  # No geo for private IPs — silently skip

    try:
        import httpx as _httpx
        async with _httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "status,lat,lon,country,city,isp"},
            )
            data = resp.json()
            if data.get("status") == "success":
                logger.debug("ip-api.com geo for %s: %s, %s", ip, data.get("city"), data.get("country"))
                return data
    except Exception as exc:
        logger.debug("ip-api.com lookup failed for %s: %s", ip, exc)
    return None


async def score_geo_deviation(
    transaction_ip: str,
    customer_home_lat: Optional[float],
    customer_home_lon: Optional[float],
    synthetic_score: float,
) -> tuple[float, str]:
    """
    Enhance geo-deviation scoring with real IP geolocation.

    Returns (score 0.0-100.0, source_label).
    Falls back to synthetic_score if real data unavailable.
    """
    if not (customer_home_lat and customer_home_lon):
        return synthetic_score, "synthetic"

    real_geo = await get_real_geo_for_ip(transaction_ip)
    if not real_geo:
        return synthetic_score, "synthetic"

    try:
        distance_km = haversine_km(
            customer_home_lat, customer_home_lon,
            real_geo["lat"], real_geo["lon"],
        )
        # Normalize: 0 km = 0 risk, 5000+ km = 100 risk
        geo_score = min(100.0, (distance_km / 5000.0) * 100.0)
        label = f"real/{real_geo.get('city', '?')},{real_geo.get('country', '?')}"
        logger.info("Real geo score for %s: %.1f km → %.1f/100 (%s)", transaction_ip, distance_km, geo_score, label)
        return geo_score, label
    except Exception as exc:
        logger.debug("Geo score calculation failed: %s", exc)
    return synthetic_score, "synthetic"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Have I Been Pwned v3 — Dark Web Breach Correlation
# ─────────────────────────────────────────────────────────────────────────────

async def check_hibp_breach(email: str, api_key: str) -> tuple[bool, int]:
    """
    Check HIBP API v3 for real breach exposure.

    Returns (is_breached: bool, breach_count: int).
    Returns (False, 0) if api_key is missing, email is empty, or any failure.

    Free key at: https://haveibeenpwned.com/API/Key
    Rate limit: varies by plan; 1.5 req/sec on basic tier.
    """
    if not api_key or not email or not _httpx_available:
        return False, 0

    try:
        import httpx as _httpx
        async with _httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers={
                    "hibp-api-key": api_key,
                    "User-Agent": "RazorpayRiskManager/2.0",
                },
                params={"truncateResponse": "true"},  # Only return breach names, not full details
            )
            if resp.status_code == 200:
                breaches = resp.json()
                count = len(breaches)
                logger.info("HIBP: %s found in %d breaches", email, count)
                return True, count
            elif resp.status_code == 404:
                logger.debug("HIBP: %s not found in any breach", email)
                return False, 0
            elif resp.status_code == 401:
                logger.warning("HIBP: Invalid API key — check HIBP_API_KEY env var")
            elif resp.status_code == 429:
                logger.warning("HIBP: Rate limited — backing off")
    except Exception as exc:
        logger.debug("HIBP lookup failed for %s: %s", email, exc)
    return False, 0


def hibp_boost_cti_score(base_score: float, breach_count: int) -> float:
    """
    Boost CTI confidence score based on confirmed breach count.
    Each breach adds 5%, capped at 0.95 (never absolute certainty from one source).
    """
    if breach_count <= 0:
        return base_score
    boost = min(0.95, base_score + (breach_count * 0.05))
    return boost


# ─────────────────────────────────────────────────────────────────────────────
# 3. AbuseIPDB — IP Reputation Scoring
# ─────────────────────────────────────────────────────────────────────────────

async def get_ip_abuse_score(ip: str, api_key: str) -> tuple[float, str]:
    """
    Get IP abuse confidence score from AbuseIPDB.

    Returns (score 0.0-1.0, isp_label).
    Returns (0.0, "unknown") if api_key is missing or any failure.

    Free key at: https://www.abuseipdb.com (1,000 checks/day).
    """
    if not api_key or not ip or not _httpx_available:
        return 0.0, "unknown"
    if _is_private_ip(ip):
        return 0.0, "private"

    try:
        import httpx as _httpx
        async with _httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(
                "https://api.abuseipdb.com/api/v2/check",
                headers={"Key": api_key, "Accept": "application/json"},
                params={"ipAddress": ip, "maxAgeInDays": "90"},
            )
            data = resp.json().get("data", {})
            score = data.get("abuseConfidenceScore", 0) / 100.0
            isp = data.get("isp", "unknown")
            usage_type = data.get("usageType", "")
            logger.info("AbuseIPDB: %s — score=%.2f isp=%s type=%s", ip, score, isp, usage_type)
            return score, isp
    except Exception as exc:
        logger.debug("AbuseIPDB lookup failed for %s: %s", ip, exc)
    return 0.0, "unknown"
