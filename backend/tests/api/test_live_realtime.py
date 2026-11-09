import hashlib
import hmac
import json
import os
import random
import time
import uuid

from fastapi.testclient import TestClient
import pytest

os.environ["WEBHOOK_SECRET"] = "dummy_webhook_secret"

from backend.api.app import app  # noqa: E402
from backend.api.routes.live import _sse  # noqa: E402
from backend.api.routes.webhooks import process_and_publish  # noqa: E402
from backend.realtime.bus import event_bus  # noqa: E402
from backend.realtime.generator import ATTACKS, TrafficGenerator  # noqa: E402

client = TestClient(app)


def _gen(tenant: str, seed: int = 7) -> TrafficGenerator:
    return TrafficGenerator(tenant, lambda: "dummy_webhook_secret", process_and_publish, rng=random.Random(seed))


def _tenant() -> str:
    return f"t_live_{uuid.uuid4().hex[:8]}"


@pytest.mark.parametrize("attack,stage", [
    ("forged_signature", "hmac"),
    ("replay_stale", "replay"),
    ("cross_tenant", "tenant"),
    ("raw_pan", "pan"),
])
def test_generator_attacks_are_blocked_by_the_right_control(attack, stage):
    tenant = _tenant()
    _gen(tenant).emit_once(attack=attack)
    ev = event_bus.recent(tenant, 1)[-1]
    assert ev["outcome"] == "REJECTED"
    assert ev["rejected_stage"] == stage
    assert ev["scenario"] == attack
    assert "4111" not in json.dumps(ev)


def test_duplicate_delivery_is_rejected_after_a_valid_event():
    tenant = _tenant()
    gen = _gen(tenant)
    gen.config.attack_ratio = 0.0
    gen.emit_once()
    gen.emit_once(attack="duplicate_delivery")
    first, second = event_bus.recent(tenant, 2)
    assert first["outcome"] == "DECIDED"
    assert second["outcome"] == "REJECTED"
    assert second["event_id"] == first["event_id"]


def test_legitimate_traffic_is_decided_through_real_pipeline():
    tenant = _tenant()
    gen = _gen(tenant, seed=1)
    gen.config.attack_ratio = 0.0
    for _ in range(20):
        gen.emit_once()
    events = event_bus.recent(tenant, 50)
    assert len(events) == 20
    assert all(e["outcome"] == "DECIDED" and e["audit_id"] for e in events)
    assert {e["decision"] for e in events} <= {"ALLOW", "REVIEW", "BLOCK", "QUARANTINE"}
    assert all(e["scenario"] not in ATTACKS for e in events)


def _post(tenant: str, data: dict, token: str | None = None) -> dict:
    payload = {"event_id": f"evt_{uuid.uuid4().hex[:12]}", "merchant_id": tenant, "timestamp": int(time.time()), "data": data}
    if token:
        payload["token"] = token
    body = json.dumps(payload).encode()
    sig = hmac.new(b"dummy_webhook_secret", body, hashlib.sha256).hexdigest()
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": tenant})
    assert resp.status_code == 200
    return resp.json()


def test_observed_velocity_raises_risk_without_caller_hint():
    tenant = _tenant()
    results = [_post(tenant, {"amount": 100, "customer_id": "cust_burst"}) for _ in range(7)]
    assert results[0]["risk_assessment"]["risk_score"] == 0
    factors = [f["name"] for f in results[-1]["risk_assessment"]["risk_factors"]]
    assert "high_velocity" in factors


def test_dead_token_reuse_is_counted_from_traffic():
    tenant = _tenant()
    first = _post(tenant, {"amount": 100, "card_lifecycle": "EXPIRED"}, token="tok_dead_1")
    assert first["zombie_signal"] is None
    second = _post(tenant, {"amount": 100, "card_lifecycle": "EXPIRED"}, token="tok_dead_1")
    assert second["zombie_signal"] is not None


def test_snapshot_is_tenant_scoped_and_accepts_query_tenant():
    tenant, other = _tenant(), _tenant()
    _post(tenant, {"amount": 100})
    _post(other, {"amount": 100})
    events = client.get("/live/snapshot", params={"tenant": tenant}).json()["events"]
    assert len(events) == 1 and events[0]["tenant_id"] == tenant
    assert client.get("/live/snapshot").status_code == 401


def test_live_endpoints_refuse_in_production(monkeypatch):
    monkeypatch.setenv("NETVRIO_ENV", "production")
    assert client.get("/live/snapshot", params={"tenant": "x"}).status_code == 501


def test_generator_controls_require_demo_mode(monkeypatch):
    monkeypatch.setenv("NETVRIO_ENV", "test")
    monkeypatch.setenv("NETVRIO_DEMO_MODE", "false")
    assert client.get("/live/generator", params={"tenant": "t"}).status_code == 404
    monkeypatch.setenv("NETVRIO_DEMO_MODE", "true")
    tenant = _tenant()
    resp = client.post("/live/generator", params={"tenant": tenant}, json={"rate_per_sec": 5, "attack_ratio": 0.3})
    assert resp.status_code == 200
    assert resp.json()["rate_per_sec"] == 5 and resp.json()["running"] is False
    assert client.post("/live/generator", params={"tenant": tenant}, json={"rate_per_sec": 999}).status_code == 422


def test_sse_frame_format():
    frame = _sse({"seq": 3, "decision": "ALLOW"})
    assert frame.startswith("id: 3\nevent: decision\ndata: ") and frame.endswith("\n\n")


# Razorpay adapter -------------------------------------------------------------------------

def _rzp_event(event="payment.captured", amount=49900, email="buyer@example.com"):
    return {
        "entity": "event", "event": event, "contains": ["payment"],
        "payload": {"payment": {"entity": {
            "id": f"pay_{uuid.uuid4().hex[:14]}", "amount": amount, "currency": "INR", "status": "captured",
            "method": "card", "email": email, "contact": "+919999999999", "token_id": "token_ABC123",
            "card": {"last4": "1111", "network": "Visa"},
        }}},
    }


def test_razorpay_webhook_unconfigured(monkeypatch):
    monkeypatch.delenv("RAZORPAY_WEBHOOK_SECRET", raising=False)
    assert client.post("/integrations/razorpay/webhook", content=b"{}").status_code == 503


def test_razorpay_webhook_rejects_bad_signature(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "rzp_test_whsec")
    body = json.dumps(_rzp_event()).encode()
    resp = client.post("/integrations/razorpay/webhook", content=body, headers={"x-razorpay-signature": "bad"})
    assert resp.status_code == 401


def test_razorpay_webhook_flows_through_pipeline_without_pii(monkeypatch):
    tenant = _tenant()
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "rzp_test_whsec")
    monkeypatch.setenv("RAZORPAY_TENANT_ID", tenant)
    body = json.dumps(_rzp_event(amount=1_500_000)).encode()  # INR 15,000 expressed in paise
    sig = hmac.new(b"rzp_test_whsec", body, hashlib.sha256).hexdigest()
    resp = client.post("/integrations/razorpay/webhook", content=body,
                       headers={"x-razorpay-signature": sig, "x-razorpay-event-id": f"evt_rzp_{uuid.uuid4().hex[:10]}"})
    assert resp.status_code == 200
    assert resp.json()["decision"] == "REVIEW"  # above the 10k threshold, so paise were converted

    ev = event_bus.recent(tenant, 1)[-1]
    assert ev["source"] == "razorpay" and ev["amount"] == 15000.0
    dumped = json.dumps(ev)
    assert "buyer@example.com" not in dumped and "+919999999999" not in dumped and "1111" not in dumped

    # Razorpay retries reuse the event id, so the replay/idempotency controls de-duplicate them.
    retry = client.post("/integrations/razorpay/webhook", content=body,
                        headers={"x-razorpay-signature": sig, "x-razorpay-event-id": ev["event_id"]})
    assert retry.status_code == 401


def test_razorpay_unsupported_event_is_acknowledged(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "rzp_test_whsec")
    body = json.dumps({"event": "refund.created", "payload": {}}).encode()
    sig = hmac.new(b"rzp_test_whsec", body, hashlib.sha256).hexdigest()
    resp = client.post("/integrations/razorpay/webhook", content=body, headers={"x-razorpay-signature": sig})
    assert resp.status_code == 200 and resp.json()["status"] == "ignored"
