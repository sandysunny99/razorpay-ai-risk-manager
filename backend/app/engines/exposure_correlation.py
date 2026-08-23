from typing import List, Dict, Any
from app.threat_intel.base import ThreatIntelProvider, ExposureMatch
from app.models.entities import Card, Customer

class ExposureCorrelationEngine:
    """
    Correlates multiple threat intelligence feeds:
    - Card fingerprint exposure (Dark web markets, Telegram stealer logs, Paste dumps)
    - BIN-level breach compromise rate
    - Customer email credential leak
    """

    def __init__(self, provider: ThreatIntelProvider):
        self.provider = provider

    async def evaluate(self, card: Card, customer: Customer) -> Dict[str, Any]:
        card_matches = await self.provider.search_card_fingerprint(card.card_fingerprint)
        bin_matches = await self.provider.search_bin_exposure(card.bin)
        email_matches = await self.provider.search_email_exposure(customer.email)

        score = 0.0
        reasons: List[str] = []
        all_matches: List[Dict[str, Any]] = []

        # 1. Direct Card Fingerprint Exposure
        if card_matches:
            # Highest confidence match determines primary weight
            max_confidence = max(m.confidence for m in card_matches)
            if max_confidence >= 0.90:
                score += 85.0 * max_confidence
                for m in card_matches:
                    reasons.append(f"High-confidence compromise ({m.confidence*100:.0f}%): Found on {m.source_name} [{m.exposure_type}]")
                    all_matches.append(m.model_dump())
            elif max_confidence >= 0.50:
                score += 50.0 * max_confidence
                for m in card_matches:
                    reasons.append(f"Medium-confidence leak match ({m.confidence*100:.0f}%): {m.source_name}")
                    all_matches.append(m.model_dump())
            else:
                score += 25.0 * max_confidence
                reasons.append(f"Low-confidence threat signal ({max_confidence*100:.0f}%): {card_matches[0].source_name}")
                all_matches.append(card_matches[0].model_dump())

        # 2. High-Risk BIN Breach
        if bin_matches:
            bin_conf = max(m.confidence for m in bin_matches)
            score += 20.0 * bin_conf
            reasons.append(f"Card BIN ({card.bin}) subject to active issuer-wide breach alert: {bin_matches[0].source_name}")
            for m in bin_matches:
                all_matches.append(m.model_dump())

        # 3. Customer Email Compromise
        if email_matches:
            score += 15.0
            reasons.append(f"Customer email ({customer.email}) identified in stealer/credential dump: {email_matches[0].source_name}")
            for m in email_matches:
                all_matches.append(m.model_dump())

        if not reasons:
            reasons.append("Zero exposure signals identified across monitored threat intelligence channels")

        normalized_score = min(100.0, score)
        return {
            "score": normalized_score,
            "reasons": reasons,
            "match_count": len(all_matches),
            "matches": all_matches
        }
