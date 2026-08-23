import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.entities import Transaction, Card, Customer, PaymentToken, SecurityCase
from app.agent.risk_agent import RiskManagerAgent
from app.threat_intel.synthetic_provider import SyntheticThreatIntelProvider
from app.threat_intel.base import ExposureMatch
from app.integrations.razorpay_adapter import MockRazorpayAdapter

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    yield db
    db.close()

@pytest.mark.asyncio
async def test_step_up_challenge_success_recalculation(test_db):
    threat_provider = SyntheticThreatIntelProvider()
    adapter = MockRazorpayAdapter()
    agent = RiskManagerAgent(db=test_db, threat_provider=threat_provider, razorpay_adapter=adapter)

    # Moderate anomaly profile (Risk ~47.0)
    fp = "fp_stepup_moderate"
    threat_provider._db[fp] = [
        ExposureMatch(
            indicator=fp,
            indicator_type="card_fingerprint",
            source_name="DarkWeb/Leak",
            exposure_type="dark_web",
            confidence=0.85,
            leak_date="2026-08-10T00:00:00Z",
            metadata={}
        )
    ]

    cust = Customer(customer_id="c_stepup_1", name="StepUp User", email="stepup@test.com", risk_tier="HIGH")
    card = Card(
        card_id="card_stepup_1", customer_id="c_stepup_1", masked_pan="**** **** **** 5521",
        card_fingerprint=fp, bin="552100", cardholder_name="StepUp User",
        expiry_month=11, expiry_year=2028, is_expired=False, status="ACTIVE"
    )
    token = PaymentToken(
        token_id="tok_stepup_1", card_id="card_stepup_1", customer_id="c_stepup_1",
        status="ACTIVE", token_age_days=30, usage_count=2
    )
    txn = Transaction(
        txn_id="txn_stepup_1", merchant_id="m_stepup", customer_id="c_stepup_1",
        card_id="card_stepup_1", token_id="tok_stepup_1", amount=16000.0,
        currency="INR", status="PENDING", ip_address="122.166.45.10",
        location_country="India", location_city="Mumbai", device_id="dev_suspicious_stepup",
        velocity_10m=4
    )

    test_db.add(cust)
    test_db.add(card)
    test_db.add(token)
    test_db.add(txn)
    test_db.commit()

    # Run investigation with simulated successful Step-Up challenge
    res = await agent.investigate_transaction("txn_stepup_1", simulate_step_up=True)

    assert res.response_tier == "STEP_UP"
    assert res.action_taken == "STEP_UP_VERIFIED_ALLOW"
    assert res.verification_status == "CHALLENGE_VERIFIED_SUCCESSFUL"
    assert res.final_risk < res.initial_risk

@pytest.mark.asyncio
async def test_dynamic_tool_selection_audit_logging(test_db):
    threat_provider = SyntheticThreatIntelProvider()
    agent = RiskManagerAgent(db=test_db, threat_provider=threat_provider)

    cust = Customer(customer_id="c_dyn_1", name="Dyn User", email="dyn@test.com", risk_tier="LOW")
    card = Card(
        card_id="card_dyn_1", customer_id="c_dyn_1", masked_pan="**** **** **** 1111",
        card_fingerprint="fp_dyn_1", bin="411111", cardholder_name="Dyn User",
        expiry_month=11, expiry_year=2028, is_expired=False, status="ACTIVE"
    )
    txn = Transaction(
        txn_id="txn_dyn_clean", merchant_id="m_dyn", customer_id="c_dyn_1",
        card_id="card_dyn_1", token_id=None, amount=300.0,
        currency="INR", status="PENDING", ip_address="122.166.45.10",
        location_country="India", location_city="Bengaluru", device_id="dev_known",
        velocity_10m=1
    )

    test_db.add(cust)
    test_db.add(card)
    test_db.add(txn)
    test_db.commit()

    res = await agent.investigate_transaction("txn_dyn_clean")

    assert res.response_tier == "LOW"
    assert res.detection_status == "CLEAN"
    assert "check_card_exposure" in res.tools_skipped
    assert "get_token" in res.tools_skipped
    assert len(res.tool_audit) > 0

    # Ensure every tool audit entry has a valid reason
    for audit_item in res.tool_audit:
        assert len(audit_item.reason) > 5
