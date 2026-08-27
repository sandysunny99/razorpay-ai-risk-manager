from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent.risk_agent import RiskManagerAgent
from app.core.config import settings
from app.core.database import get_db
from app.engines.token_risk import TokenRiskEngine
from app.models.entities import Card, PaymentToken, SecurityCase
from app.models.schemas import InvestigationRequest, InvestigationResponse, OverviewMetrics
from app.threat_intel.synthetic_provider import SyntheticThreatIntelProvider

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
        req.transaction_id = "TXN-2026-9042"

    try:
        response = await agent.investigate_transaction(req.transaction_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/step-up/request")
async def request_step_up(transaction_id: str, db: Session = Depends(get_db)):
    """Initiates a simulated 2FA Step-Up Challenge for a suspicious transaction."""
    from app.integrations.razorpay_adapter import MockRazorpayAdapter
    adapter = MockRazorpayAdapter()
    challenge = await adapter.request_step_up_challenge(transaction_id)
    return challenge

@router.post("/step-up/verify")
async def verify_step_up(challenge_id: str, transaction_id: str, success: bool = True, db: Session = Depends(get_db)):
    """Verifies a Step-Up Challenge and re-evaluates transaction risk post-challenge."""
    agent = RiskManagerAgent(db=db, threat_provider=threat_provider)
    res = await agent.investigate_transaction(transaction_id, simulate_step_up=success)
    return {
        "challenge_id": challenge_id,
        "transaction_id": transaction_id,
        "verified": success,
        "status": "VERIFIED_SUCCESSFUL" if success else "CHALLENGE_FAILED",
        "investigation": res
    }

