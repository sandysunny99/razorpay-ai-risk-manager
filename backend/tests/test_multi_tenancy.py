import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agent.risk_agent import RiskManagerAgent
from app.core.database import Base
from app.db.seed_data import seed_initial_data
from app.threat_intel.synthetic_provider import SyntheticThreatIntelProvider


@pytest.fixture
def multi_tenant_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    seed_initial_data(db)
    yield db
    db.close()

@pytest.mark.asyncio
async def test_multi_tenant_authorized_merchant_access(multi_tenant_db):
    agent = RiskManagerAgent(db=multi_tenant_db, threat_provider=SyntheticThreatIntelProvider())
    # Transaction TXN-2026-9042 belongs to DemoStore
    res = await agent.investigate_transaction("TXN-2026-9042", merchant_id="DemoStore")
    assert res.initial_risk == 94.0
    assert res.final_risk < 25.0
    assert res.final_severity == "LOW"

@pytest.mark.asyncio
async def test_multi_tenant_idor_cross_merchant_access_denied(multi_tenant_db):
    agent = RiskManagerAgent(db=multi_tenant_db, threat_provider=SyntheticThreatIntelProvider())
    # Attempting to access DemoStore's transaction using merchant_id='merchant_attacker_99'
    with pytest.raises(PermissionError) as exc_info:
        await agent.investigate_transaction("TXN-2026-9042", merchant_id="merchant_attacker_99")

    assert "Multi-Tenant Security Violation" in str(exc_info.value)

def test_multi_tenant_case_isolation_query(multi_tenant_db):
    from app.models.entities import SecurityCase
    # Add a case for DemoStore
    c = SecurityCase(
        case_id="CASE-TEST-01", severity="HIGH", card_id="card_4921",
        customer_id="cust_1042", merchant_id="DemoStore", risk_score=80.0,
        reason="Test isolation case"
    )
    multi_tenant_db.add(c)
    multi_tenant_db.commit()

    # Query cases scoped strictly to DemoStore
    cases_demo = multi_tenant_db.query(SecurityCase).filter(SecurityCase.merchant_id == "DemoStore").all()
    # Query cases for another non-existent merchant
    cases_other = multi_tenant_db.query(SecurityCase).filter(SecurityCase.merchant_id == "CompetitorMerchant").all()
    assert len(cases_demo) >= 1
    assert len(cases_other) == 0

def test_multi_tenant_token_vault_scoping(multi_tenant_db):
    from app.models.entities import PaymentToken
    tokens_demo = multi_tenant_db.query(PaymentToken).filter(PaymentToken.merchant_id == "DemoStore").all()
    tokens_other = multi_tenant_db.query(PaymentToken).filter(PaymentToken.merchant_id == "UnregisteredMerchant").all()
    assert len(tokens_demo) >= 3
    assert len(tokens_other) == 0
