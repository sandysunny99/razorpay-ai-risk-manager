import hashlib
import hmac
import importlib.util
import json
import os
from pathlib import Path
import time
import uuid

from fastapi.testclient import TestClient
import pytest

os.environ["WEBHOOK_SECRET"] = "dummy_webhook_secret"

from backend.api.app import app  # noqa: E402
from backend.realtime.bus import event_bus  # noqa: E402
from backend.realtime.generator import synthetic_pan  # noqa: E402
from backend.security.card_reference import CardReferenceProtector, ReferenceMode  # noqa: E402

client = TestClient(app)
FP_SECRET_HEX = "a1" * 32
FEED_SECRET = "exposure_feed_test_secret"

_spec = importlib.util.spec_from_file_location(
    "onionclaw_exposure_adapter", Path(__file__).resolve().parents[3] / "scripts" / "onionclaw_exposure_adapter.py"
)
adapter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adapter)


def _tenant() -> str:
    return f"t_exp_{uuid.uuid4().hex[:8]}"


def _post(tenant: str, data: dict, token=None, fingerprint=None):
    payload = {"event_id": f"evt_{uuid.uuid4().hex[:12]}", "merchant_id": tenant, "timestamp": int(time.time()), "data": data}
    if token:
        payload["token"] = token
    if fingerprint:
        payload["fingerprint"] = fingerprint
    body = json.dumps(payload).encode()
    sig = hmac.new(b"dummy_webhook_secret", body, hashlib.sha256).hexdigest()
    return client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": tenant})


def _report(findings, ts=None, secret=FEED_SECRET):
    body = json.dumps({"source": "onionclaw", "findings": findings}).encode()
    ts = str(ts if ts is not None else int(time.time()))
    sig = "sha256=" + hmac.new(secret.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
    return client.post("/intel/exposures", content=body,
                       headers={"x-netvrio-timestamp": ts, "x-netvrio-signature": sig, "content-type": "application/json"})


# ── adapter ─────────────────────────────────────────────────────────────────────────────────

def test_adapter_fingerprint_matches_backend_scheme(monkeypatch):
    monkeypatch.setenv("FINGERPRINT_HMAC_SECRET", FP_SECRET_HEX)
    pan = synthetic_pan("tok_any")
    backend_fp = CardReferenceProtector(allow_raw_reference=True).normalize(pan, ReferenceMode.APPROVED_FINGERPRINT)
    assert adapter.fingerprint(bytes.fromhex(FP_SECRET_HEX), pan) == backend_fp


def test_adapter_extracts_only_luhn_valid_numbers_and_never_outputs_them(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("FINGERPRINT_HMAC_SECRET", FP_SECRET_HEX)
    good = synthetic_pan("tok_a")
    spaced = " ".join([synthetic_pan("tok_b")[i:i + 4] for i in range(0, 16, 4)])
    bad = good[:-1] + str((int(good[-1]) + 1) % 10)  # broken check digit
    dump = tmp_path / "dump.json"
    dump.write_text(json.dumps([
        {"url": "http://exampleabc123456.onion/thread/55", "text": f"cc|{good}|12/29 and {spaced}"},
        {"url": "http://other.onion/x", "text": f"not a card {bad}, phone 9999999999, 0000000000000000"},
    ]))
    findings = adapter.collect([dump], bytes.fromhex(FP_SECRET_HEX))
    assert len(findings) == 2
    assert {f["reference"] for f in findings} == {"exampleabc#.onion"}
    assert adapter.main([str(dump)]) == 0
    out = capsys.readouterr().out
    assert good not in out and synthetic_pan("tok_b") not in out and "2 exposed card fingerprint" in out


def test_adapter_refuses_plain_http_to_remote_hosts():
    with pytest.raises(ValueError):
        adapter.post_findings("http://netvrio.example/intel/exposures", [{"fingerprint": "fp_" + "0" * 16}], "s")
    with pytest.raises(ValueError):
        adapter.post_findings("file:///etc/passwd", [{"fingerprint": "fp_" + "0" * 16}], "s")


# ── ingestion + enforcement ─────────────────────────────────────────────────────────────────

def test_exposure_report_revokes_linked_tokens_and_blocks_next_use(monkeypatch):
    monkeypatch.setenv("EXPOSURE_FEED_SECRET", FEED_SECRET)
    tenant = _tenant()
    fp = "fp_" + uuid.uuid4().hex[:16]
    token = f"tok_{uuid.uuid4().hex[:8]}"
    assert _post(tenant, {"amount": 100}, token=token, fingerprint=fp).json()["decision"] == "ALLOW"

    resp = _report([{"fingerprint": fp, "reference": "leaksite.onion", "confidence": 0.95}])
    assert resp.status_code == 200
    assert resp.json() == {"accepted": 1, "new": 1, "tokens_revoked": 1}
    assert any(e["outcome"] == "EXPOSURE" for e in event_bus.recent(tenant, 5))

    # Token alone (no fingerprint on the request): blocked by the proactive revocation.
    blocked = _post(tenant, {"amount": 100}, token=token).json()
    assert blocked["decision"] == "BLOCK"
    cats = {m["category"] for m in blocked["threat_intel"]}
    assert "card_exposed" in cats or "revoked_token" in cats
    # A brand-new token presenting the exposed fingerprint is blocked inline.
    fresh = _post(tenant, {"amount": 100}, token=f"tok_{uuid.uuid4().hex[:8]}", fingerprint=fp).json()
    assert fresh["decision"] == "BLOCK" and fresh["zombie_signal"]["recommendation"] == "REVOKE_TOKEN"


def test_exposure_ingestion_rejects_bad_auth_stale_and_pan_like_data(monkeypatch):
    monkeypatch.setenv("EXPOSURE_FEED_SECRET", FEED_SECRET)
    fp = "fp_" + "ab" * 8
    assert _report([{"fingerprint": fp}], secret="wrong").status_code == 401
    assert _report([{"fingerprint": fp}], ts=int(time.time()) - 3600).status_code == 401
    assert _report([{"fingerprint": synthetic_pan("tok_x")}]).status_code == 400  # a PAN is not a fingerprint
    assert _report([{"fingerprint": fp, "reference": "dump " + synthetic_pan("tok_y")}]).status_code == 400


def test_exposure_ingestion_requires_configuration(monkeypatch):
    monkeypatch.delenv("EXPOSURE_FEED_SECRET", raising=False)
    assert _report([{"fingerprint": "fp_" + "cd" * 8}]).status_code == 503


# ── YouPI-PG ────────────────────────────────────────────────────────────────────────────────

def _youpi(body: dict, secret="youpi_test_secret", ts=None, v2=True, delivery=None):
    raw = json.dumps(body).encode()
    ts = str(ts if ts is not None else int(time.time() * 1000))
    sign = lambda msg: "sha256=" + hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()  # noqa: E731
    headers = {"x-gateway-signature": sign(raw), "x-gateway-timestamp": ts,
               "x-gateway-delivery-id": delivery or str(uuid.uuid4()), "content-type": "application/json"}
    if v2:
        headers["x-gateway-signature-v2"] = sign(ts.encode() + b"." + raw)
    return client.post("/integrations/youpi/webhook", content=raw, headers=headers)


def _upi_body(event="OBSERVED_SUCCESS", paise=1_200_000):
    return {"event": event, "settlementState": "RECONCILED" if event == "RECONCILED" else "NOT_RECONCILED",
            "orderId": "ord_1", "amount": f"{paise / 100:.2f}", "amountPaise": paise, "utr": "123456789012",
            "paymentId": str(uuid.uuid4()), "payerVpa": "someone@upi"}


def test_youpi_observed_payment_flows_and_is_marked_unreconciled(monkeypatch):
    tenant = _tenant()
    monkeypatch.setenv("YOUPI_WEBHOOK_SECRET", "youpi_test_secret")
    monkeypatch.setenv("YOUPI_TENANT_ID", tenant)
    delivery = str(uuid.uuid4())
    resp = _youpi(_upi_body(), delivery=delivery)
    assert resp.status_code == 200 and resp.json()["decision"] == "REVIEW"  # INR 12,000 > 10k
    ev = event_bus.recent(tenant, 1)[-1]
    assert ev["source"] == "youpi" and ev["event_type"] == "upi.observed_success" and ev["amount"] == 12000.0
    assert "someone@upi" not in json.dumps(ev) and "123456789012" not in json.dumps(ev)
    # Retry of the same delivery: acknowledged, not processed twice.
    again = _youpi(_upi_body(), delivery=delivery)
    assert again.status_code == 200 and again.json()["status"] == "duplicate"


def test_youpi_signature_v2_and_freshness(monkeypatch):
    monkeypatch.setenv("YOUPI_WEBHOOK_SECRET", "youpi_test_secret")
    assert _youpi(_upi_body(), secret="wrong").status_code == 401
    assert _youpi(_upi_body(), ts=int(time.time() * 1000) - 3 * 3600 * 1000).status_code == 401
    monkeypatch.setenv("YOUPI_REQUIRE_V2", "true")
    assert _youpi(_upi_body(), v2=False).status_code == 401


def test_youpi_unsupported_event_and_unconfigured(monkeypatch):
    monkeypatch.setenv("YOUPI_WEBHOOK_SECRET", "youpi_test_secret")
    assert _youpi({"event": "ORDER_CREATED"}).json()["status"] == "ignored"
    monkeypatch.delenv("YOUPI_WEBHOOK_SECRET")
    assert client.post("/integrations/youpi/webhook", content=b"{}").status_code == 503
