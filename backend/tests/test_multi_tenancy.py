from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agent.risk_agent import RiskManagerAgent
from app.core.auth import Role, create_access_token, enforce_tenant_access
from app.core.database import Base, get_db
from app.db.seed_data import seed_initial_data
from app.engines.audit_ledger import AuditLedgerEngine
from app.main import app
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


def test_enforce_tenant_access_logic():
    """Verify enforce_tenant_access allows matching tenant, allows admin override, and blocks mismatched tenant."""
    # 1. Matching merchant: permitted
    analyst_claims = {"username": "analyst", "role": Role.ANALYST.value, "merchant_id": "MerchantAlpha"}
    assert enforce_tenant_access("MerchantAlpha", analyst_claims) == "MerchantAlpha"
    assert enforce_tenant_access(None, analyst_claims) == "MerchantAlpha"

    # 2. Mismatched merchant: HTTP 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        enforce_tenant_access("MerchantBeta", analyst_claims)
    assert exc_info.value.status_code == 403
    assert "scoped to merchant 'MerchantAlpha'" in exc_info.value.detail

    # 3. System Admin: cross-tenant access permitted
    admin_claims = {"username": "admin", "role": Role.ADMIN.value, "merchant_id": "default"}
    assert enforce_tenant_access("MerchantBeta", admin_claims) == "MerchantBeta"


def test_cross_merchant_audit_events_endpoint(multi_tenant_db):
    """Verify /api/v1/audit/events enforces tenant isolation and blocks cross-merchant access."""
    # Add audit event for MerchantAlpha and MerchantBeta
    AuditLedgerEngine.append_event(
        db=multi_tenant_db,
        event_id="AUD-ALPHA-01",
        actor="AlphaAgent",
        decision="ALLOW",
        risk_score=10.0,
        policy="P1",
        tool=None,
        action_requested="ALLOW",
        action_executed="ALLOW",
        verification="VERIFIED",
        details={"tenant": "alpha"},
        merchant_id="MerchantAlpha"
    )
    AuditLedgerEngine.append_event(
        db=multi_tenant_db,
        event_id="AUD-BETA-01",
        actor="BetaAgent",
        decision="BLOCK",
        risk_score=90.0,
        policy="P2",
        tool=None,
        action_requested="BLOCK",
        action_executed="BLOCK",
        verification="VERIFIED",
        details={"tenant": "beta"},
        merchant_id="MerchantBeta"
    )

    app.dependency_overrides[get_db] = lambda: multi_tenant_db
    client = TestClient(app)

    # Merchant Alpha Analyst token
    token_alpha = create_access_token(subject="alpha_user", role=Role.ANALYST, merchant_id="MerchantAlpha")

    # 1. Normal query: only returns Alpha's audit events
    resp = client.get(
        "/api/v1/audit/events",
        headers={"Authorization": f"Bearer {token_alpha}"}
    )
    assert resp.status_code == 200
    events = resp.json()
    assert any(e["event_id"] == "AUD-ALPHA-01" for e in events)
    assert not any(e["event_id"] == "AUD-BETA-01" for e in events)

    # 2. Forged query attempting to access MerchantBeta's events: returns 403 Forbidden
    forged_resp = client.get(
        "/api/v1/audit/events?merchant_id=MerchantBeta",
        headers={"Authorization": f"Bearer {token_alpha}"}
    )
    assert forged_resp.status_code == 403
    assert "scoped to merchant 'MerchantAlpha'" in forged_resp.json()["detail"]

    app.dependency_overrides.pop(get_db, None)
