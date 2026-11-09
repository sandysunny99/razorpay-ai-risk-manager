"""Feature contract shared by training (evaluation/*.jsonl) and live scoring.

Only behavioural and lifecycle signals are used. Identifiers (customer, merchant, card
fingerprint) and free-text sources are excluded so the model cannot memorise entities or leak
labels through provenance strings.
"""
import math
from typing import Any, Dict, List, Optional

FEATURES: List[str] = [
    "log_amount",
    "velocity",
    "country_mismatch",
    "card_exposed",
    "exposure_confidence",
    "token_active",
    "token_age_days",
    "is_zombie_token",
    "card_expired",
    "device_new",
    "failed_attempts",
]

# Live traffic often cannot supply these; training masks them at random so the model learns to
# score with them missing instead of reading "unknown" as zero.
OFTEN_MISSING = ["country_mismatch", "token_age_days", "device_new", "failed_attempts"]

NAN = float("nan")


def _num(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)) and not (isinstance(value, float) and math.isnan(value)):
        return float(value)
    return NAN


def from_training_row(r: Dict[str, Any]) -> List[float]:
    return [
        math.log1p(max(0.0, float(r["amount"]))),
        _num(r["velocity_10m"]),
        1.0 if r["country"] != r["customer_country"] else 0.0,
        _num(r["card_exposed"]),
        _num(r["exposure_confidence"]),
        _num(r["token_active"]),
        _num(r["token_age_days"]),
        _num(r["is_zombie_token"]),
        _num(r["card_expired"]),
        _num(r["device_new"]),
        _num(r["failed_attempts_count"]),
    ]


def from_live_event(
    *,
    amount: Any,
    velocity: Optional[int],
    data: Dict[str, Any],
    exposure_confidence: Optional[float],
    token_revoked: bool,
    zombie_signals: List[str],
    lifecycle: Optional[str],
) -> List[float]:
    country = data.get("country")
    customer_country = data.get("customer_country")
    mismatch = NAN
    if isinstance(country, str) and isinstance(customer_country, str):
        mismatch = 1.0 if country.upper() != customer_country.upper() else 0.0
    amt = _num(amount)
    return [
        math.log1p(max(0.0, amt)) if not math.isnan(amt) else NAN,
        _num(velocity),
        mismatch,
        1.0 if exposure_confidence is not None else 0.0,
        float(exposure_confidence) if exposure_confidence is not None else 0.0,
        0.0 if token_revoked else 1.0,
        _num(data.get("token_age_days")),
        1.0 if zombie_signals else 0.0,
        1.0 if str(lifecycle or "").upper() == "EXPIRED" else 0.0,
        _num(data.get("device_new")),
        _num(data.get("failed_attempts")),
    ]


READABLE = {
    "log_amount": "payment amount",
    "velocity": "recent payment velocity",
    "country_mismatch": "country differs from customer's",
    "card_exposed": "card reported exposed",
    "exposure_confidence": "exposure confidence",
    "token_active": "token state",
    "token_age_days": "token age",
    "is_zombie_token": "zombie token signal",
    "card_expired": "card expired",
    "device_new": "new device",
    "failed_attempts": "recent failed attempts",
}
