from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Card, ExposureEvent
from app.threat_intel.synthetic_provider import SyntheticThreatIntelProvider

router = APIRouter(prefix="/exposure", tags=["Card Exposure & CTI"])
threat_provider = SyntheticThreatIntelProvider()

@router.get("/events")
def list_exposure_events(
    limit: int = Query(50, description="Max records to return"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Lists threat intelligence breach correlation events without exposing raw PANs."""
    events = db.query(ExposureEvent).order_by(ExposureEvent.created_at.desc()).limit(limit).all()
    results = []
    for ev in events:
        results.append({
            "id": ev.id,
            "card_fingerprint": ev.card_fingerprint[:12] + "...",
            "bin": ev.bin,
            "source_name": ev.source_name,
            "exposure_type": ev.exposure_type,
            "confidence_score": ev.confidence_score,
            "leak_date": ev.leak_date.isoformat() if ev.leak_date else None,
            "created_at": ev.created_at.isoformat() if ev.created_at else None
        })
    return results

@router.get("/statistics")
def get_exposure_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns aggregated card exposure metrics across monitored inventory."""
    total_cards = db.query(Card).count()
    exposed_count = db.query(ExposureEvent).count()
    stealer_count = db.query(ExposureEvent).filter(ExposureEvent.exposure_type == "stealer_log").count()
    paste_count = db.query(ExposureEvent).filter(ExposureEvent.exposure_type == "paste_leak").count()

    return {
        "cards_monitored": total_cards,
        "cards_exposed": min(total_cards, exposed_count),
        "stealer_dump_matches": stealer_count,
        "paste_leak_matches": paste_count,
        "active_cti_sources": 4,
        "provider_status": "ONLINE (Synthetic Offline Provider)"
    }

@router.post("/check")
def check_card_exposure(payload: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Checks if a card fingerprint exists in CTI breach feeds.
    Zero raw PAN accepted; expects HMAC-SHA256 fingerprint or card_id.
    """
    fp = payload.get("card_fingerprint")
    card_id = payload.get("card_id")

    if not fp and card_id:
        card = db.query(Card).filter(Card.card_id == card_id).first()
        if card:
            fp = card.card_fingerprint

    if not fp:
        return {"matched": False, "confidence": 0.0, "exposure_count": 0, "sources": []}

    matches = threat_provider.search_card_exposure(fp)
    return {
        "matched": len(matches) > 0,
        "confidence": max([m.confidence for m in matches]) if matches else 0.0,
        "exposure_count": len(matches),
        "sources": [m.source_name for m in matches]
    }
