import hashlib
import hmac
import json
import os
from pathlib import Path
import time
import uuid

from fastapi.testclient import TestClient
import pytest

os.environ["WEBHOOK_SECRET"] = "dummy_webhook_secret"

from backend.api.app import app  # noqa: E402
from backend.llm.schemas import _ip_network  # noqa: E402
from backend.ml.features import FEATURES, from_live_event  # noqa: E402
from backend.ml.scorer import MlScorer, ml_scorer  # noqa: E402
from backend.policy.engine import PolicyEngine  # noqa: E402
from backend.policy.models import MerchantPolicy, SecurityValidationResult  # noqa: E402
from backend.risk.models import ActionDecision, RiskAssessment  # noqa: E402
from backend.security.pii import _regex_scrub, pii_scrubber  # noqa: E402

client = TestClient(app)
lightgbm = pytest.importorskip("lightgbm")


def _post(tenant: str, data: dict, token=None):
    payload = {"event_id": f"evt_{uuid.uuid4().hex[:12]}", "merchant_id": tenant, "timestamp": int(time.time()), "data": data}
    if token:
        payload["token"] = token
    body = json.dumps(payload).encode()
    sig = hmac.new(b"dummy_webhook_secret", body, hashlib.sha256).hexdigest()
    return client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": tenant})


def _live(**kw):
    base = dict(amount=500, velocity=1, data={}, exposure_confidence=None, token_revoked=False, zombie_signals=[], lifecycle="ACTIVE")
    base.update(kw)
    return from_live_event(**base)


# ── ML second opinion ───────────────────────────────────────────────────────────────────────

def test_model_ranks_live_style_cases_sensibly():
    ordinary = ml_scorer.score(_live())["probability"]
    zombie = ml_scorer.score(_live(zombie_signals=["EXPIRED_CARD_REUSE"], lifecycle="EXPIRED"))["probability"]
    exposed = ml_scorer.score(_live(exposure_confidence=0.9, data={"device_new": True}))["probability"]
    # Regression for the shortcut found in the bundled dataset: zombie at normal velocity must score high.
    assert zombie > 0.8 > ordinary
    assert exposed > 0.8


def test_reasons_are_tree_shap_contributions():
    res = ml_scorer.score(_live(velocity=9, data={"failed_attempts": 4, "device_new": True}, amount=20))
    assert res["reasons"] and all(r["direction"] in ("raises", "lowers") for r in res["reasons"])
    assert res["reasons"][0]["direction"] == "raises"


def test_scorer_fails_safe_without_model(tmp_path):
    broken = MlScorer(model_path=tmp_path / "missing.txt")
    assert broken.score([0.0] * len(FEATURES)) is None
    assert broken.available is False and broken.error


def test_policy_ml_escalation_only_turns_allow_into_review():
    engine = PolicyEngine()
    policy = MerchantPolicy(merchant_id="m", auto_block_threshold=90.0, auto_review_threshold=50.0, require_step_up_for_zombie=True)
    sec = SecurityValidationResult(is_valid_signature=True, is_idempotent=True, is_not_replayed=True, is_valid_tenant=True)

    def assess(score):
        return RiskAssessment(risk_level="LOW", risk_score=score, confidence=1.0, risk_factors=[], evidence_ids=["e"], correlation_id="c", timestamp=1)

    low = engine.evaluate(assess(0.0), policy, sec, ml_escalation=True)
    assert low.decision == ActionDecision.REVIEW and "ML_SECOND_OPINION_REVIEW" in low.reason_codes
    high = engine.evaluate(assess(95.0), policy, sec, ml_escalation=True)
    assert high.decision == ActionDecision.BLOCK  # never relaxed, never the reason for a block
    assert "ML_SECOND_OPINION_REVIEW" not in high.reason_codes


def test_pipeline_escalation_is_opt_in(monkeypatch):
    tenant = f"t_ml_{uuid.uuid4().hex[:6]}"
    data = {"amount": 50, "failed_attempts": 5, "device_new": True}
    monkeypatch.setenv("NETVRIO_ML_ESCALATE", "false")
    off = _post(tenant, {**data, "customer_id": "c1"}).json()
    assert off["decision"] == "ALLOW" and off["ml_assessment"]["probability"] >= 0.8 and off["ml_assessment"]["escalated"] is False
    monkeypatch.setenv("NETVRIO_ML_ESCALATE", "true")
    on = _post(tenant, {**data, "customer_id": "c2"}).json()
    assert on["decision"] == "REVIEW" and on["ml_assessment"]["escalated"] is True
    assert "ML_SECOND_OPINION_REVIEW" in client.get(f"/audit/{on['audit_id']}", headers={"x-tenant-id": tenant}).json()["reason_codes"]


def test_model_card_records_honest_metrics():
    card = json.loads((Path(__file__).resolve().parents[2] / "ml" / "model" / "model_card.json").read_text())
    assert card["why_not_evaluation_set"]["label_rule_agreement"] == 1.0
    assert 0.5 < card["holdout_metrics"]["pr_auc"] < 1.0  # noisy simulator: perfection would be a red flag
    assert "synthetic" in card["caveat"].lower()


# ── PII masking ─────────────────────────────────────────────────────────────────────────────

SAMPLE = ("Call +91 9876543210 or mail rahul.s@example.com, pay rahul@okaxis. Card 4111 1111 1111 1111, "
          "PAN ABCPE1234F, Aadhaar 2345 6789 0123 from 49.36.10.2")


@pytest.mark.parametrize("engine", ["regex", "auto"])
def test_free_text_pii_is_masked(engine, monkeypatch):
    masked, found = _regex_scrub(SAMPLE) if engine == "regex" else pii_scrubber.scrub(SAMPLE)
    for raw in ("9876543210", "rahul.s@example.com", "rahul@okaxis", "4111 1111 1111 1111", "ABCPE1234F", "2345 6789 0123", "49.36.10.2"):
        assert raw not in masked
    assert {"CREDIT_CARD", "EMAIL_ADDRESS", "UPI_ID", "IN_MOBILE", "IN_PAN", "IN_AADHAAR"} <= set(found)


def test_non_luhn_numbers_and_plain_text_are_left_alone():
    text = "order 1234567890123 refund for invoice 77"
    assert _regex_scrub(text)[0] == text


def test_pipeline_masks_notes_everywhere():
    tenant = f"t_pii_{uuid.uuid4().hex[:6]}"
    resp = _post(tenant, {"amount": 100, "note": "customer said pay me at rahul@okaxis or +91 9876543210"}).json()
    assert {"UPI_ID", "IN_MOBILE"} <= set(resp["pii_masked"])
    from backend.realtime.bus import event_bus
    dumped = json.dumps(event_bus.recent(tenant, 1)) + json.dumps(resp)
    assert "rahul@okaxis" not in dumped and "9876543210" not in dumped


def test_llm_never_receives_raw_ip():
    assert _ip_network("49.36.10.2") == "49.36.10.0/24"
    assert _ip_network("not-an-ip") == "unknown"


def test_components_endpoint_reports_engines():
    body = client.get("/health/components").json()
    assert body["pii"]["engine"] in ("presidio", "regex")
    assert body["ml"]["available"] is True and "holdout_metrics" in body["ml"]


# ── Rate limiting ───────────────────────────────────────────────────────────────────────────

def test_ingest_endpoints_are_rate_limited(monkeypatch):
    from backend.api.ratelimit import limiter

    limiter.reset()
    monkeypatch.setenv("NETVRIO_RATE_LIMIT", "3/minute")
    codes = [client.post("/webhooks/payment", content=b"{}", headers={"x-tenant-id": "t_rl"}).status_code for _ in range(5)]
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]
    limiter.reset()
