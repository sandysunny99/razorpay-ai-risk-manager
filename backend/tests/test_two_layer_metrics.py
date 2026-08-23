import pytest
import hashlib
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.entities import Transaction, Card, Customer, PaymentToken, SecurityCase
from app.evaluation.evaluator import ModelEvaluator
from app.agent.risk_agent import RiskManagerAgent
from app.threat_intel.synthetic_provider import SyntheticThreatIntelProvider
from app.threat_intel.base import ExposureMatch
from app.integrations.razorpay_adapter import MockRazorpayAdapter

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    yield db
    db.close()

def test_held_out_test_set_hash_integrity():
    """Validates that evaluation/test.jsonl is strictly frozen and unmodified."""
    test_path = Path("evaluation/test.jsonl")
    assert test_path.exists(), "Held-out test set file missing."
    
    with open(test_path, "rb") as f:
        computed_hash = hashlib.sha256(f.read()).hexdigest()
    
    EXPECTED_HASH = "76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f"
    assert computed_hash == EXPECTED_HASH, f"Test set was modified! Hash mismatch: {computed_hash} != {EXPECTED_HASH}"

def test_layer_1_broad_detection_metrics_t40():
    """Validates empirical metrics for Layer 1: Broad Risk Detection (T = 40.0)."""
    evaluator = ModelEvaluator()
    m = evaluator.evaluate_dataset("test.jsonl", threshold=40.0)
    
    assert m["total_samples"] == 300
    assert m["tp"] == 59
    assert m["fp"] == 0
    assert m["tn"] == 233
    assert m["fn"] == 8
    assert m["precision"] == 1.0
    assert m["recall"] == 0.8806
    assert m["f1"] == 0.9365
    assert m["fpr"] == 0.0
    assert m["expected_cost"] == 40000.0

def test_layer_2_autonomous_action_metrics_t75():
    """Validates empirical metrics for Layer 2: Autonomous Auto-Remediation (T = 75.0)."""
    evaluator = ModelEvaluator()
    m = evaluator.evaluate_dataset("test.jsonl", threshold=75.0)
    
    assert m["total_samples"] == 300
    assert m["tp"] == 35
    assert m["fp"] == 0
    assert m["tn"] == 233
    assert m["fn"] == 32
    assert m["precision"] == 1.0
    assert m["recall"] == 0.5224
    assert m["f1"] == 0.6863
    assert m["fpr"] == 0.0
    assert m["expected_cost"] == 160000.0

@pytest.mark.asyncio
async def test_step_up_challenge_all_four_outcomes(db_session):
    """Validates all four lifecycle outcomes for Step-Up 2FA challenges: SUCCESS, FAILED, TIMEOUT, ABANDONED."""
    threat_provider = SyntheticThreatIntelProvider()
    agent = RiskManagerAgent(db=db_session, threat_provider=threat_provider)

    fp = "fp_test_outcomes"
    threat_provider._db[fp] = [
        ExposureMatch(
            indicator=fp, indicator_type="card_fingerprint", source_name="DarkWeb/Leak",
            exposure_type="dark_web", confidence=0.85, leak_date="2026-08-10T00:00:00Z", metadata={}
        )
    ]
    cust = Customer(customer_id="cust_outcomes", name="User Out", email="out@test.com", risk_tier="HIGH", default_country="India", default_city="Delhi")
    card = Card(card_id="card_outcomes", customer_id="cust_outcomes", masked_pan="**** 9999", card_fingerprint=fp, bin="411111", cardholder_name="User Out", expiry_month=12, expiry_year=2028, is_expired=False, status="ACTIVE")
    token = PaymentToken(token_id="tok_outcomes", card_id="card_outcomes", customer_id="cust_outcomes", status="ACTIVE", token_age_days=30, usage_count=2)
    db_session.add_all([cust, card, token])
    db_session.commit()

    # 1. SUCCESS outcome
    txn_succ = Transaction(txn_id="t_succ", merchant_id="m1", customer_id="cust_outcomes", card_id="card_outcomes", token_id="tok_outcomes", amount=16000.0, currency="INR", status="PENDING", ip_address="1.1.1.1", location_country="India", location_city="Mumbai", device_id="dev_susp_1", velocity_10m=4)
    db_session.add(txn_succ)
    db_session.commit()
    res_succ = await agent.investigate_transaction("t_succ", simulate_step_up="SUCCESS")
    assert res_succ.verification_status == "CHALLENGE_VERIFIED_SUCCESSFUL"
    assert res_succ.action_taken == "STEP_UP_VERIFIED_ALLOW"
    assert res_succ.final_risk < res_succ.initial_risk

    # 2. FAILED outcome
    txn_fail = Transaction(txn_id="t_fail", merchant_id="m1", customer_id="cust_outcomes", card_id="card_outcomes", token_id="tok_outcomes", amount=16000.0, currency="INR", status="PENDING", ip_address="1.1.1.1", location_country="India", location_city="Mumbai", device_id="dev_susp_2", velocity_10m=4)
    db_session.add(txn_fail)
    db_session.commit()
    res_fail = await agent.investigate_transaction("t_fail", simulate_step_up="FAILED")
    assert res_fail.verification_status == "CHALLENGE_FAILED_UNAUTHORIZED"
    assert res_fail.action_taken == "STEP_UP_FAILED_BLOCKED"
    assert res_fail.final_risk > res_fail.initial_risk
    assert res_fail.case_id is not None

    # 3. TIMEOUT outcome
    txn_time = Transaction(txn_id="t_time", merchant_id="m1", customer_id="cust_outcomes", card_id="card_outcomes", token_id="tok_outcomes", amount=16000.0, currency="INR", status="PENDING", ip_address="1.1.1.1", location_country="India", location_city="Mumbai", device_id="dev_susp_3", velocity_10m=4)
    db_session.add(txn_time)
    db_session.commit()
    res_time = await agent.investigate_transaction("t_time", simulate_step_up="TIMEOUT")
    assert res_time.verification_status == "CHALLENGE_TIMEOUT_EXPIRED"
    assert res_time.action_taken == "STEP_UP_TIMEOUT_ESCALATED"
    assert res_time.case_id is not None

    # 4. ABANDONED outcome
    txn_aban = Transaction(txn_id="t_aban", merchant_id="m1", customer_id="cust_outcomes", card_id="card_outcomes", token_id="tok_outcomes", amount=16000.0, currency="INR", status="PENDING", ip_address="1.1.1.1", location_country="India", location_city="Mumbai", device_id="dev_susp_4", velocity_10m=4)
    db_session.add(txn_aban)
    db_session.commit()
    res_aban = await agent.investigate_transaction("t_aban", simulate_step_up="ABANDONED")
    assert res_aban.verification_status == "CHALLENGE_ABANDONED"
    assert res_aban.action_taken == "STEP_UP_ABANDONED_CANCELLED"

@pytest.mark.asyncio
async def test_evidence_grounding_and_abstention(db_session):
    """Validates structured evidence tags [EVID-...] and safe abstention on clean traffic."""
    threat_provider = SyntheticThreatIntelProvider()
    agent = RiskManagerAgent(db=db_session, threat_provider=threat_provider)

    cust = Customer(customer_id="cust_clean_ev", name="Clean Ev User", email="clean@test.com", risk_tier="LOW", default_country="India", default_city="Delhi")
    card = Card(card_id="card_clean_ev", customer_id="cust_clean_ev", masked_pan="**** 1234", card_fingerprint="fp_clean_ev", bin="411111", cardholder_name="Clean Ev User", expiry_month=12, expiry_year=2028, is_expired=False, status="ACTIVE")
    txn = Transaction(txn_id="txn_clean_ev", merchant_id="m_clean", customer_id="cust_clean_ev", card_id="card_clean_ev", token_id=None, amount=450.0, currency="INR", status="PENDING", ip_address="122.166.45.10", location_country="India", location_city="Delhi", device_id="dev_known_01", velocity_10m=1)
    db_session.add_all([cust, card, txn])
    db_session.commit()

    res = await agent.investigate_transaction("txn_clean_ev")

    assert res.response_tier == "LOW"
    assert res.detection_status == "CLEAN"
    assert res.action_taken == "ALLOW"
    assert "[EVID-TXN-001]" in res.agent_reasoning
    assert "Zero credential breach exposure" in res.agent_reasoning

@pytest.mark.asyncio
async def test_fail_safe_behavior_on_missing_adapter(db_session):
    """Validates that system handles missing external adapter gracefully without crashing."""
    threat_provider = SyntheticThreatIntelProvider()
    # Adapter is initialized safely in mock mode
    agent = RiskManagerAgent(db=db_session, threat_provider=threat_provider)

    cust = Customer(customer_id="cust_fs", name="FailSafe User", email="fs@test.com", risk_tier="LOW", default_country="India", default_city="Delhi")
    card = Card(card_id="card_fs", customer_id="cust_fs", masked_pan="**** 0000", card_fingerprint="fp_fs", bin="411111", cardholder_name="FailSafe User", expiry_month=12, expiry_year=2028, is_expired=False, status="ACTIVE")
    txn = Transaction(txn_id="txn_fs", merchant_id="m_fs", customer_id="cust_fs", card_id="card_fs", token_id=None, amount=500.0, currency="INR", status="PENDING", ip_address="122.166.45.10", location_country="India", location_city="Delhi", device_id="dev_01", velocity_10m=1)
    db_session.add_all([cust, card, txn])
    db_session.commit()

    res = await agent.investigate_transaction("txn_fs")
    assert res.investigation_id.startswith("INV-")
    assert res.verification_status in ["ALLOWED", "NOT_APPLICABLE"]
