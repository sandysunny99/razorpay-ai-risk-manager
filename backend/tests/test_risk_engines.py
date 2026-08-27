from app.engines.risk_scorer import RiskScoringEngine
from app.engines.token_risk import TokenRiskEngine
from app.engines.transaction_risk import TransactionRiskEngine
from app.models.entities import Card, Customer, PaymentToken, Transaction


def test_transaction_risk_high_anomaly():
    engine = TransactionRiskEngine()
    cust = Customer(
        customer_id="c1", name="Arjun", email="a@ex.com",
        default_country="India", default_city="Bengaluru"
    )
    # Critical amount, foreign geo, velocity 4
    txn = Transaction(
        txn_id="t1", customer_id="c1", card_id="cd1",
        amount=18500.0, location_city="Moscow", location_country="Russia",
        velocity_10m=4, device_id="dev_suspicious_01"
    )
    res = engine.evaluate(txn, cust)
    assert res["score"] >= 80.0
    assert any("amount" in r.lower() for r in res["reasons"])
    assert any("geographic mismatch" in r.lower() for r in res["reasons"])
    assert any("velocity" in r.lower() for r in res["reasons"])

def test_transaction_risk_clean():
    engine = TransactionRiskEngine()
    cust = Customer(
        customer_id="c1", name="Arjun", email="a@ex.com",
        default_country="India", default_city="Bengaluru"
    )
    txn = Transaction(
        txn_id="t2", customer_id="c1", card_id="cd1",
        amount=500.0, location_city="Bengaluru", location_country="India",
        velocity_10m=1, device_id="dev_trusted_01"
    )
    res = engine.evaluate(txn, cust)
    assert res["score"] == 0.0

def test_zombie_token_detection():
    token_engine = TokenRiskEngine()
    # Expired Card
    card_expired = Card(
        card_id="c_exp", customer_id="c1", masked_pan="**** **** **** 8820",
        card_fingerprint="fp1", bin="520082", cardholder_name="Priya",
        expiry_month=1, expiry_year=2023, is_expired=True, status="EXPIRED"
    )
    # Active Token
    token_active = PaymentToken(
        token_id="tok_zombie_1", card_id="c_exp", customer_id="c1",
        status="ACTIVE", token_age_days=100, usage_count=10
    )

    eval_res = token_engine.evaluate(token_active, card_expired)
    assert eval_res["is_zombie"] is True
    assert eval_res["score"] >= 80.0
    assert "ZOMBIE TOKEN" in eval_res["zombie_reason"]

def test_risk_scorer_weights_and_severity():
    scorer = RiskScoringEngine()
    txn_res = {"score": 80.0, "reasons": ["Amount anomaly"]}
    exp_res = {"score": 90.0, "reasons": ["Telegram leak"]}
    crd_res = {"score": 0.0, "reasons": []}
    tok_res = {"score": 15.0, "reasons": []}

    result = scorer.calculate(txn_res, exp_res, crd_res, tok_res)
    assert result["composite_score"] >= 75.0
    assert result["severity"] == "CRITICAL"
    assert len(result["factors"]) == 6
