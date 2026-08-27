import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agent.risk_agent import RiskManagerAgent
from app.core.database import Base
from app.models.entities import Card, Customer, PaymentToken, Transaction
from app.threat_intel.base import ExposureMatch
from app.threat_intel.synthetic_provider import SyntheticThreatIntelProvider


@pytest.fixture
def benchmark_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    yield db
    db.close()

@pytest.mark.asyncio
async def test_agent_100_scenario_dynamic_trajectory_benchmark(benchmark_db):
    """
    Simulates 100 diverse transaction scenarios across 4 distinct archetype profiles:
    - Profile A (50% Clean / Low Risk): Fast screening, Level 0, skips heavy CTI.
    - Profile B (20% Moderate / Step-Up): Velocity & device friction, Level 2 Step-Up 2FA.
    - Profile C (10% Zombie Token): Expired card with active token, Level 3 Zombie lifecycle remediation.
    - Profile D (20% Critical Compromise): Multi-signal dark-web attack, Level 3 Autonomous Revocation & Verification.
    """
    threat_provider = SyntheticThreatIntelProvider()
    agent = RiskManagerAgent(db=benchmark_db, threat_provider=threat_provider)

    cust_low = Customer(customer_id="cust_bench_low", name="Bench Low", email="low@test.com", risk_tier="LOW", default_country="India", default_city="Delhi")
    cust_med = Customer(customer_id="cust_bench_med", name="Bench Med", email="med@test.com", risk_tier="MEDIUM", default_country="India", default_city="Delhi")
    benchmark_db.add(cust_low)
    benchmark_db.add(cust_med)

    completed_runs = 0
    correct_tier_runs = 0
    verified_action_runs = 0
    total_tools_executed = 0
    total_tools_skipped = 0

    for i in range(100):
        card_id = f"c_bench_{i}"
        token_id = f"tok_bench_{i}"
        txn_id = f"txn_bench_{i}"

        # Scenario distribution
        if i < 50:
            scenario_type = "CLEAN"
            cust_id = "cust_bench_low"
        elif i < 70:
            scenario_type = "STEP_UP"
            cust_id = "cust_bench_med"
        elif i < 80:
            scenario_type = "ZOMBIE"
            cust_id = "cust_bench_low"
        else:
            scenario_type = "CRITICAL"
            cust_id = "cust_bench_low"

        fp = f"fp_bench_{i}_{scenario_type.lower()}"

        is_expired = (scenario_type == "ZOMBIE")
        is_attack = (scenario_type == "CRITICAL")
        is_step_up = (scenario_type == "STEP_UP")

        if is_attack:
            threat_provider._db[fp] = [
                ExposureMatch(
                    indicator=fp,
                    indicator_type="card_fingerprint",
                    source_name="Telegram/RedLine-Stealer-Dump",
                    exposure_type="stealer_log",
                    confidence=0.96,
                    leak_date="2026-08-20T14:22:00Z",
                    metadata={"malware_tag": "Win32.Redline"}
                )
            ]
        elif is_step_up:
            threat_provider._db[fp] = [
                ExposureMatch(
                    indicator=fp,
                    indicator_type="card_fingerprint",
                    source_name="Pastebin/Leak",
                    exposure_type="paste",
                    confidence=0.85,
                    leak_date="2026-08-15T00:00:00Z",
                    metadata={}
                )
            ]

        card = Card(
            card_id=card_id,
            customer_id=cust_id,
            masked_pan=f"**** **** **** {1000+i}",
            card_fingerprint=fp,
            bin="411111",
            cardholder_name="Bench User",
            expiry_month=1,
            expiry_year=2020 if is_expired else 2028,
            is_expired=is_expired,
            status="EXPIRED" if is_expired else "ACTIVE"
        )
        token = PaymentToken(
            token_id=token_id,
            card_id=card_id,
            customer_id=cust_id,
            status="ACTIVE",
            token_age_days=60,
            usage_count=5
        )

        if scenario_type == "CRITICAL":
            amount = 18500.0
            velocity = 4
            country = "Russia"
            city = "Moscow"
            device = f"dev_foreign_{i}"
        elif scenario_type == "STEP_UP":
            amount = 16000.0
            velocity = 4
            country = "India"
            city = "Mumbai"
            device = f"dev_suspicious_{i}"
        elif scenario_type == "ZOMBIE":
            amount = 1200.0
            velocity = 1
            country = "India"
            city = "Delhi"
            device = f"dev_{i}"
        else: # CLEAN
            amount = 500.0
            velocity = 1
            country = "India"
            city = "Delhi"
            device = f"dev_{i}"

        txn = Transaction(
            txn_id=txn_id,
            merchant_id="m_bench",
            customer_id=cust_id,
            card_id=card_id,
            token_id=token_id,
            amount=amount,
            currency="INR",
            status="PENDING",
            ip_address="195.201.12.88" if is_attack else "122.166.45.10",
            location_country=country,
            location_city=city,
            device_id=device,
            velocity_10m=velocity
        )

        benchmark_db.add(card)
        benchmark_db.add(token)
        benchmark_db.add(txn)
        benchmark_db.commit()

        resp = await agent.investigate_transaction(txn_id)
        completed_runs += 1
        total_tools_executed += len(resp.tools_executed)
        total_tools_skipped += len(resp.tools_skipped)

        if scenario_type == "CLEAN":
            if resp.response_tier == "LOW" and resp.action_taken == "ALLOW":
                correct_tier_runs += 1
                assert "check_card_exposure" in resp.tools_skipped
        elif scenario_type == "STEP_UP":
            if resp.response_tier == "STEP_UP" and resp.action_taken == "REQUEST_STEP_UP":
                correct_tier_runs += 1
        elif scenario_type == "ZOMBIE":
            if resp.response_tier == "AUTO_REMEDIATE" and resp.verification_status == "VERIFIED_SUCCESSFUL":
                correct_tier_runs += 1
                verified_action_runs += 1
        elif scenario_type == "CRITICAL":
            if resp.response_tier == "AUTO_REMEDIATE" and resp.verification_status == "VERIFIED_SUCCESSFUL":
                correct_tier_runs += 1
                verified_action_runs += 1

    completion_rate = completed_runs / 100.0
    tier_accuracy = correct_tier_runs / 100.0

    assert completion_rate == 1.0
    assert tier_accuracy == 1.0
    assert verified_action_runs == 30  # 10 Zombie + 20 Critical
    assert total_tools_skipped > 0  # Proves dynamic tool selection
