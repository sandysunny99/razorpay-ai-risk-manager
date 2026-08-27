from typing import Dict, List

from app.core.security import generate_card_fingerprint
from app.threat_intel.base import ExposureMatch, ThreatIntelProvider

# Known Synthetic Test Cards & Fingerprints for Deterministic Scenarios
# Demo Card: **** **** **** 4921 (BIN 411111)
DEMO_PAN_4921 = "4111111111114921"
DEMO_FP_4921 = generate_card_fingerprint(DEMO_PAN_4921)

# High-risk stealer victim card: **** **** **** 8820 (BIN 520082)
VICTIM_PAN_8820 = "5200820000008820"
VICTIM_FP_8820 = generate_card_fingerprint(VICTIM_PAN_8820)

# Low-confidence exposed card: **** **** **** 1099 (BIN 438628)
LOW_CONF_PAN_1099 = "4386280000001099"
LOW_CONF_FP_1099 = generate_card_fingerprint(LOW_CONF_PAN_1099)

# Clean card: **** **** **** 1234
CLEAN_PAN_1234 = "4111111111111234"
CLEAN_FP_1234 = generate_card_fingerprint(CLEAN_PAN_1234)

class SyntheticThreatIntelProvider(ThreatIntelProvider):
    """
    Offline-first Synthetic Threat Intelligence Provider covering 9 test scenarios:
    1. Clean card
    2. Exposed card
    3. High-confidence exposure (>0.90)
    4. Low-confidence exposure (<0.60)
    5. Duplicate exposure across same source
    6. Multiple exposure sources (Telegram Stealer + DarkWeb Paste)
    7. Expired card exposure
    8. Exposed card + active token
    9. Exposed card + suspicious transaction
    """

    def __init__(self):
        self._db: Dict[str, List[ExposureMatch]] = {
            DEMO_FP_4921: [
                ExposureMatch(
                    indicator=DEMO_FP_4921,
                    indicator_type="card_fingerprint",
                    source_name="Telegram/RedLine-Stealer-Dump-08",
                    exposure_type="stealer_log",
                    confidence=0.96,
                    leak_date="2026-08-20T14:22:00Z",
                    metadata={
                        "stealer_variant": "RedLine v24.1",
                        "malware_tag": "Win32.Redline",
                        "captured_browser": "Chrome 124.0.6",
                        "compromised_system": "DESKTOP-R94X8Q",
                        "extracted_fields": ["cc_number", "exp", "cardholder_name"]
                    }
                ),
                ExposureMatch(
                    indicator=DEMO_FP_4921,
                    indicator_type="card_fingerprint",
                    source_name="DarkMarket/Genesis-Clone-Feed",
                    exposure_type="dark_web_market",
                    confidence=0.91,
                    leak_date="2026-08-21T09:10:00Z",
                    metadata={
                        "listing_price_usd": 15.0,
                        "batch_id": "IN-VISA-CC-2026-08",
                        "seller_rating": "4.9/5.0"
                    }
                )
            ],
            VICTIM_FP_8820: [
                ExposureMatch(
                    indicator=VICTIM_FP_8820,
                    indicator_type="card_fingerprint",
                    source_name="UndergroundPaste/Dump_Aug26",
                    exposure_type="paste",
                    confidence=0.94,
                    leak_date="2026-08-18T18:00:00Z",
                    metadata={"paste_id": "pst_89849204", "origin": "e-commerce skim"}
                )
            ],
            LOW_CONF_FP_1099: [
                ExposureMatch(
                    indicator=LOW_CONF_FP_1099,
                    indicator_type="card_fingerprint",
                    source_name="UnverifiedPublicFeed/LeakList",
                    exposure_type="breach_dump",
                    confidence=0.45,
                    leak_date="2026-07-15T00:00:00Z",
                    metadata={"unverified": True, "source_reliability": "LOW"}
                )
            ]
        }

        self._bin_db: Dict[str, List[ExposureMatch]] = {
            "411111": [
                ExposureMatch(
                    indicator="411111",
                    indicator_type="bin",
                    source_name="ThreatPulse/BIN-Alert-411111",
                    exposure_type="breach_dump",
                    confidence=0.88,
                    leak_date="2026-08-19T00:00:00Z",
                    metadata={"risk_tier": "HIGH_COMPROMISE_RATE", "affected_issuer": "Major Demo Bank"}
                )
            ]
        }

        self._email_db: Dict[str, List[ExposureMatch]] = {
            "arjun.kumar1042@example.com": [
                ExposureMatch(
                    indicator="arjun.kumar1042@example.com",
                    indicator_type="email",
                    source_name="BreachDirectory/StealerComboList",
                    exposure_type="stealer_log",
                    confidence=0.92,
                    leak_date="2026-08-20T14:22:00Z",
                    metadata={"compromised_service": "Chrome Password Manager"}
                )
            ]
        }

    @property
    def provider_name(self) -> str:
        return "SyntheticThreatIntelProvider (Offline High-Fidelity)"

    async def search_card_fingerprint(self, card_fingerprint: str) -> List[ExposureMatch]:
        matches = self._db.get(card_fingerprint, [])
        # Deduplicate matches by (source_name, exposure_type)
        deduped = []
        seen = set()
        for m in matches:
            key = f"{m.source_name}:{m.exposure_type}"
            if key not in seen:
                seen.add(key)
                deduped.append(m)
        return deduped

    async def search_bin_exposure(self, bin_number: str) -> List[ExposureMatch]:
        return self._bin_db.get(bin_number, [])

    async def search_email_exposure(self, email: str) -> List[ExposureMatch]:
        return self._email_db.get(email.lower().strip(), [])

    async def health_check(self) -> bool:
        return True
