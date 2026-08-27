from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.entities import (
    Card,
    CloudflareSecurityEvent,
    Customer,
    ExposureEvent,
    PaymentToken,
    Transaction,
    User,
)
from app.threat_intel.synthetic_provider import CLEAN_FP_1234, DEMO_FP_4921, VICTIM_FP_8820


def seed_initial_data(db: Session):
    """Seed comprehensive initial test data for all demo scenarios."""
    if db.query(Customer).count() > 0:
        return  # Already seeded

    # 1. Customers
    c1 = Customer(
        customer_id="cust_1042",
        name="Arjun Kumar",
        email="arjun.kumar1042@example.com",
        risk_tier="LOW",
        default_country="India",
        default_city="Bengaluru"
    )
    c2 = Customer(
        customer_id="cust_2089",
        name="Priya Sharma",
        email="priya.sharma2089@example.com",
        risk_tier="LOW",
        default_country="India",
        default_city="Mumbai"
    )
    c3 = Customer(
        customer_id="cust_3110",
        name="Rohan Verma",
        email="rohan.verma@example.com",
        risk_tier="HIGH",
        default_country="India",
        default_city="Delhi"
    )
    db.add_all([c1, c2, c3])
    db.commit()

    # 2. Cards
    card1 = Card(
        card_id="card_4921",
        customer_id="cust_1042",
        masked_pan="**** **** **** 4921",
        card_fingerprint=DEMO_FP_4921,
        bin="411111",
        cardholder_name="Arjun Kumar",
        expiry_month=12,
        expiry_year=2028,
        is_expired=False,
        status="ACTIVE",
        failed_attempts=1,
        previous_fraud_count=0
    )
    # Zombie Card (Expired Card with Active Token)
    card_zombie = Card(
        card_id="card_zombie_8820",
        customer_id="cust_2089",
        masked_pan="**** **** **** 8820",
        card_fingerprint=VICTIM_FP_8820,
        bin="520082",
        cardholder_name="Priya Sharma",
        expiry_month=5,
        expiry_year=2024,  # Past date
        is_expired=True,
        status="EXPIRED",
        failed_attempts=0,
        previous_fraud_count=0
    )
    card_clean = Card(
        card_id="card_clean_1234",
        customer_id="cust_3110",
        masked_pan="**** **** **** 1234",
        card_fingerprint=CLEAN_FP_1234,
        bin="411111",
        cardholder_name="Rohan Verma",
        expiry_month=10,
        expiry_year=2029,
        is_expired=False,
        status="ACTIVE",
        failed_attempts=0,
        previous_fraud_count=0
    )
    db.add_all([card1, card_zombie, card_clean])
    db.commit()

    # 3. Payment Tokens
    tok1 = PaymentToken(
        token_id="tok_test_123",
        card_id="card_4921",
        customer_id="cust_1042",
        merchant_id="DemoStore",
        status="ACTIVE",
        token_age_days=18,
        usage_count=12,
        last_used_at=datetime.now(timezone.utc)
    )
    # ZOMBIE TOKEN: ACTIVE on EXPIRED card
    tok_zombie = PaymentToken(
        token_id="tok_zombie_999",
        card_id="card_zombie_8820",
        customer_id="cust_2089",
        merchant_id="DemoStore",
        status="ACTIVE",
        token_age_days=450,
        usage_count=84,
        last_used_at=datetime.now(timezone.utc) - timedelta(hours=2)
    )
    tok_clean = PaymentToken(
        token_id="tok_clean_456",
        card_id="card_clean_1234",
        customer_id="cust_3110",
        merchant_id="DemoStore",
        status="ACTIVE",
        token_age_days=5,
        usage_count=2,
        last_used_at=datetime.now(timezone.utc)
    )
    db.add_all([tok1, tok_zombie, tok_clean])
    db.commit()

    # 4. Golden Demo Transaction: Anomaly + Foreign Geo + High Velocity
    txn_golden = Transaction(
        txn_id="TXN-2026-9042",
        customer_id="cust_1042",
        card_id="card_4921",
        token_id="tok_test_123",
        merchant_id="DemoStore",
        amount=18500.0,
        currency="INR",
        status="PENDING",
        ip_address="195.201.12.88",
        location_city="Moscow",
        location_country="Russia",
        device_id="dev_suspicious_x89",
        velocity_10m=4
    )
    txn_normal = Transaction(
        txn_id="TXN-2026-1001",
        customer_id="cust_3110",
        card_id="card_clean_1234",
        token_id="tok_clean_456",
        merchant_id="DemoStore",
        amount=850.0,
        currency="INR",
        status="SUCCESS",
        ip_address="122.166.45.10",
        location_city="Delhi",
        location_country="India",
        device_id="dev_trusted_01",
        velocity_10m=1
    )
    db.add_all([txn_golden, txn_normal])
    db.commit()

    # 5. Threat Intelligence Exposure Events
    exp1 = ExposureEvent(
        card_fingerprint=DEMO_FP_4921,
        bin="411111",
        source_name="RedLine_Stealer_DarkWeb_Forum",
        exposure_type="stealer_log",
        confidence_score=0.96,
        leak_date=datetime.now(timezone.utc) - timedelta(days=2),
        raw_metadata={"bot_net": "RedLine_v24", "origin_country": "RU"}
    )
    exp2 = ExposureEvent(
        card_fingerprint=VICTIM_FP_8820,
        bin="520082",
        source_name="Pastebin_Breach_Leak",
        exposure_type="paste_leak",
        confidence_score=0.74,
        leak_date=datetime.now(timezone.utc) - timedelta(days=7),
        raw_metadata={"paste_id": "paste_8820_dump"}
    )
    db.add_all([exp1, exp2])
    db.commit()

    # 6. Cloudflare Security Telemetry Events
    cf1 = CloudflareSecurityEvent(
        event_id="CF-EVT-9042A",
        ray_id="8c41f0a12e9b-BOM",
        masked_ray_id="8c41...2e9b",
        tenant_id="DemoStore",
        event_type="WAF_INSPECT",
        origin_ip="195.201.12.88",
        country="RU",
        waf_action="ALLOW",
        bot_score=15,
        bot_signal="LIKELY_AUTOMATED",
        rate_limit_signal="ALLOW",
        tls_version="TLSv1.3",
        edge_status="NORMAL"
    )
    cf2 = CloudflareSecurityEvent(
        event_id="CF-EVT-1001B",
        ray_id="8c41f0a12e9c-DEL",
        masked_ray_id="8c41...2e9c",
        tenant_id="DemoStore",
        event_type="WAF_INSPECT",
        origin_ip="122.166.45.10",
        country="IN",
        waf_action="ALLOW",
        bot_score=92,
        bot_signal="LIKELY_HUMAN",
        rate_limit_signal="ALLOW",
        tls_version="TLSv1.3",
        edge_status="NORMAL"
    )
    db.add_all([cf1, cf2])

    # 7. Default System Users (Admin, Analyst, Viewer, Merchant B)
    if db.query(User).count() == 0:
        u_admin = User(
            user_id="usr_admin_01",
            username="admin",
            email="admin@riskmanager.razorpay.internal",
            hashed_password=hash_password("AdminRisk@2026!"),
            role="admin",
            merchant_id="default",
            is_active=True
        )
        u_analyst = User(
            user_id="usr_analyst_01",
            username="analyst",
            email="analyst@riskmanager.razorpay.internal",
            hashed_password=hash_password("AnalystRisk@2026!"),
            role="operator",
            merchant_id="default",
            is_active=True
        )
        u_viewer = User(
            user_id="usr_viewer_01",
            username="viewer",
            email="viewer@riskmanager.razorpay.internal",
            hashed_password=hash_password("ViewerRisk@2026!"),
            role="viewer",
            merchant_id="default",
            is_active=True
        )
        u_merchant_b = User(
            user_id="usr_mer_b_01",
            username="merchant_b_analyst",
            email="analyst@merchantb.internal",
            hashed_password=hash_password("MerchantB@2026!"),
            role="operator",
            merchant_id="merchant_b",
            is_active=True
        )
        db.add_all([u_admin, u_analyst, u_viewer, u_merchant_b])

    db.commit()
