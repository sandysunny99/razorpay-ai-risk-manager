import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.entities import SecurityCase, AuditEvent, PaymentToken
from app.db.seed_data import seed_initial_data
from app.threat_intel.synthetic_provider import SyntheticThreatIntelProvider
from app.agent.risk_agent import RiskManagerAgent

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_initial_data(db)
    yield db
    db.close()

@pytest.mark.asyncio
async def test_golden_demo_scenario_workflow(test_db):
    threat_provider = SyntheticThreatIntelProvider()
    agent = RiskManagerAgent(db=test_db, threat_provider=threat_provider)
    
    # Execute autonomous investigation on golden demo transaction
    response = await agent.investigate_transaction("TXN-2026-9042")
    
    # 1. Check Initial State
    assert response.initial_risk == 94.0
    assert response.initial_severity == "CRITICAL"
    
    # 2. Check Policy & Action
    assert response.policy_status == "AUTO_EXECUTE"
    assert "REVOKE_TOKEN" in response.action_taken
    
    # 3. Check Verification & Recalculation
    assert response.verification_status == "VERIFIED_SUCCESSFUL"
    assert response.final_risk < 30.0
    assert response.final_severity == "LOW"
    
    # 4. Check Timeline Stages
    stages = [s.stage for s in response.timeline]
    expected_stages = ["OBSERVE", "DETECT", "INVESTIGATE", "CORRELATE", "ASSESS_RISK", "POLICY_CHECK", "ACT", "VERIFY", "RECALCULATE", "AUDIT"]
    for st in expected_stages:
        assert st in stages
        
    # 5. Check Case and Audit DB records
    case = test_db.query(SecurityCase).filter(SecurityCase.case_id == response.case_id).first()
    assert case is not None
    assert case.status == "OPEN"
    assert case.severity == "CRITICAL"
    
    audit = test_db.query(AuditEvent).first()
    assert audit is not None
    assert audit.action_executed.startswith("REVOKE_TOKEN")
