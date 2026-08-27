from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.engines.card_risk import CardRiskEngine
from app.engines.exposure_correlation import ExposureCorrelationEngine
from app.models.entities import Card, Customer, PaymentToken
from app.models.schemas import CardResponse
from app.threat_intel.synthetic_provider import SyntheticThreatIntelProvider

router = APIRouter(prefix="/cards", tags=["Cards"])
threat_provider = SyntheticThreatIntelProvider()

@router.get("", response_model=List[CardResponse])
async def list_cards(db: Session = Depends(get_db)):
    cards = db.query(Card).all()
    resp = []
    card_engine = CardRiskEngine()
    exposure_engine = ExposureCorrelationEngine(threat_provider)

    for card in cards:
        token_count = db.query(PaymentToken).filter(PaymentToken.card_id == card.card_id).count()
        customer = db.query(Customer).filter(Customer.customer_id == card.customer_id).first()

        crd_eval = card_engine.evaluate(card)
        exp_eval = await exposure_engine.evaluate(card, customer) if customer else {"score": 0.0, "match_count": 0}

        risk_score = round(min(100.0, (crd_eval["score"] * 0.4) + (exp_eval["score"] * 0.6)), 1)

        resp.append(CardResponse(
            card_id=card.card_id,
            customer_id=card.customer_id,
            masked_pan=card.masked_pan,
            bin=card.bin,
            cardholder_name=card.cardholder_name,
            expiry_month=card.expiry_month,
            expiry_year=card.expiry_year,
            is_expired=card.is_expired,
            status=card.status,
            failed_attempts=card.failed_attempts,
            previous_fraud_count=card.previous_fraud_count,
            active_token_count=token_count,
            exposure_count=exp_eval["match_count"],
            current_risk_score=risk_score
        ))
    return resp
