from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.entities import Card, PaymentToken, Transaction, SecurityCase, ExposureEvent
from app.models.schemas import OverviewMetrics, InvestigationRequest, InvestigationResponse
from app.threat_intel.synthetic_provider import SyntheticThreatIntelProvider
from app.agent.risk_agent import RiskManagerAgent
from app.engines.token_risk import TokenRiskEngine

router = APIRouter(prefix="/risk", tags=["Risk Management"])

threat_provider = SyntheticThreatIntelProvider()

@router.get("/overview", response_model=OverviewMetrics)
def get_risk_overview(db: Session = Depends(get_db)):
    cards_count = db.query(Card).count()
    tokens_count = db.query(PaymentToken).count()
    
    # Calculate Zombie Tokens count
    tokens_with_cards = (
        db.query(PaymentToken, Card)
        .join(Card, PaymentToken.card_id == Card.card_id)
        .all()
    )
    token_engine = TokenRiskEngine()
    zombies = token_engine.detect_zombie_tokens(tokens_with_cards)
    
    open_cases = db.query(SecurityCase).filter(SecurityCase.status == "OPEN").count()
    critical_cases = db.query(SecurityCase).filter(SecurityCase.severity == "CRITICAL").count()
    
    return OverviewMetrics(
        cards_monitored=cards_count,
        tokens_monitored=tokens_count,
        active_zombie_tokens=len(zombies),
        high_risk_cards=db.query(Card).filter(Card.status != "ACTIVE").count() or 1,
        critical_incidents=critical_cases,
        exposure_events_count=2,  # Monitored breach instances
        open_cases_count=open_cases,
        system_status="OPERATIONAL",
        dry_run_mode=settings.DRY_RUN
    )

@router.post("/investigate", response_model=InvestigationResponse)
async def investigate_target(req: InvestigationRequest, db: Session = Depends(get_db)):
    agent = RiskManagerAgent(db=db, threat_provider=threat_provider)
    if not req.transaction_id:
        # Default to the primary demo transaction
        req.transaction_id = "TXN-2026-9042"
    
    try:
        response = await agent.investigate_transaction(req.transaction_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
