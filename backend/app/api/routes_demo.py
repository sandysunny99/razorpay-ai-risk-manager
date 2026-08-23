from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db, Base, engine
from app.agent.risk_agent import RiskManagerAgent
from app.threat_intel.synthetic_provider import SyntheticThreatIntelProvider
from app.db.seed_data import seed_initial_data
from app.models.schemas import InvestigationResponse

router = APIRouter(prefix="/demo", tags=["Demo Controller"])
threat_provider = SyntheticThreatIntelProvider()

@router.get("/scenarios")
def get_available_scenarios():
    return [
        {
            "id": "golden_compromise",
            "name": "Golden Hackathon Scenario: Exposed Card + Active Token + High-Value Anomaly",
            "description": "Customer 1042 card **** 4921 used for ₹18,500 from Moscow (Velocity: 4 attempts). Stealer log match found. Initial risk: 94/100 (CRITICAL). Policy permits token revocation. Token revoked, risk drops to 21/100 (LOW).",
            "txn_id": "TXN-2026-9042",
            "card_masked": "**** **** **** 4921",
            "expected_initial_risk": 94.0,
            "expected_final_risk": 21.0
        },
        {
            "id": "zombie_token_scan",
            "name": "Zombie Token Detection: Active Token on Expired Card",
            "description": "Token tok_zombie_999 is ACTIVE on expired card **** 8820 (Exp 05/2024). Scanned and detected as critical recurring liability.",
            "card_masked": "**** **** **** 8820",
            "expected_risk": "CRITICAL / HIGH"
        },
        {
            "id": "clean_transaction",
            "name": "Clean Benchmark: Domestic ₹850 Transaction",
            "description": "Customer 3110 card **** 1234 used for ₹850 in Delhi on trusted device. Risk: 0/100 (LOW). Zero remediation required.",
            "txn_id": "TXN-2026-1001",
            "card_masked": "**** **** **** 1234",
            "expected_initial_risk": 0.0,
            "expected_final_risk": 0.0
        }
    ]

@router.post("/trigger-golden-scenario", response_model=InvestigationResponse)
async def trigger_golden_scenario(db: Session = Depends(get_db)):
    """
    Executes the definitive Razorpay Hackathon Risk Workflow:
    1. Transaction arrives (₹18,500, Moscow, 4 attempts)
    2. Deterministic Anomaly detected (+20 Amount, +15 Geo, +14 Velocity)
    3. Zero-knowledge Card Exposure match on Telegram Stealer (+25)
    4. Active Token risk (+10) -> Composite Risk = 94/100 (CRITICAL)
    5. Policy evaluated: Token revocation AUTO_EXECUTE allowed; Card suspension REVIEW_REQUIRED
    6. Agent revokes token tok_test_123 on Razorpay adapter
    7. Verification Engine queries vault -> Confirmed REVOKED
    8. Risk recalculated: drops 94 -> 21
    9. Security Case & Audit Log created
    """
    agent = RiskManagerAgent(db=db, threat_provider=threat_provider)
    return await agent.investigate_transaction("TXN-2026-9042")

@router.post("/reset-data")
def reset_demo_database(db: Session = Depends(get_db)):
    """Reset the database to clean demo state."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_initial_data(db)
    return {"status": "SUCCESS", "message": "Demo database successfully reset and seeded."}
