import hashlib
import hmac
import ipaddress
import json
import os
import time
import uuid

from fastapi.testclient import TestClient

os.environ["WEBHOOK_SECRET"] = "dummy_webhook_secret"

from backend.api.app import app  # noqa: E402
from backend.realtime.bus import event_bus  # noqa: E402
from backend.threat_intel import feeds  # noqa: E402
from backend.threat_intel.service import ThreatIntelService  # noqa: E402
from backend.threat_intel.store import IndicatorStore, mask_ip, parse_public_networks  # noqa: E402

client = TestClient(app)


def _tenant() -> str:
    return f"t_ti_{uuid.uuid4().hex[:8]}"


def _post(tenant: str, data: dict, token: str | None = None):
    payload = {"event_id": f"evt_{uuid.uuid4().hex[:12]}", "merchant_id": tenant, "timestamp": int(time.time()), "data": data}
    if token:
        payload["token"] = token
    body = json.dumps(payload).encode()
    sig = hmac.new(b"dummy_webhook_secret", body, hashlib.sha256).hexdigest()
    return client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": tenant})


# ── parsing safety ──────────────────────────────────────────────────────────────────────────

def test_feed_parser_drops_private_bogon_broad_and_garbage_entries():
    nets = parse_public_networks([
        "10.0.0.0/8", "192.168.1.1", "100.64.0.0/10", "127.0.0.1",    # non-global
        "0.0.0.0/0", "4.0.0.0/6",                                     # absurdly broad
        "not-an-ip", "1.2.3.4/33", "",                                # garbage
        "185.220.101.1", "45.95.0.0/16 ; SBL123", "198.51.100.0/24",  # valid (incl. doc range)
    ])
    assert [str(n) for n in nets] == ["185.220.101.1/32", "45.95.0.0/16", "198.51.100.0/24"]


def test_spamhaus_ndjson_and_legacy_formats():
    text = '{"cidr":"45.95.0.0/16","sblid":"SBL1"}\n; comment\n{"type":"metadata"}\n103.1.2.0/24 ; SBL2\n'
    assert feeds._parse_spamhaus(text) == ["45.95.0.0/16", "103.1.2.0/24 ; SBL2"]


def test_ip_masking_keeps_only_network():
    assert mask_ip(ipaddress.ip_address("198.51.100.77")) == "198.51.100.0/24"


# ── matching and pipeline integration ───────────────────────────────────────────────────────

def test_listed_ip_adds_risk_evidence_and_policy_reviews():
    tenant = _tenant()
    resp = _post(tenant, {"amount": 100, "ip_address": "198.51.100.77"})
    assert resp.status_code == 200
    body = resp.json()
    factors = [f["name"] for f in body["risk_assessment"]["risk_factors"]]
    assert "threat_intel_botnet" in factors
    assert body["decision"] == "REVIEW"
    assert body["threat_intel"][0]["source"] == "netvrio-synthetic"
    # Raw IP never leaves the pipeline: response and live event carry only the masked network.
    assert "198.51.100.77" not in json.dumps(body)
    assert "198.51.100.77" not in json.dumps(event_bus.recent(tenant, 1))


def test_unlisted_and_malformed_ips_do_not_match():
    tenant = _tenant()
    clean = _post(tenant, {"amount": 100, "ip_address": "100.70.1.2"}).json()
    junk = _post(tenant, {"amount": 100, "ip_address": "<script>"}).json()
    assert clean["threat_intel"] == [] and clean["decision"] == "ALLOW"
    assert junk["threat_intel"] == [] and junk["decision"] == "ALLOW"


def test_zombie_revocation_is_enforced_on_next_use():
    tenant = _tenant()
    first = _post(tenant, {"amount": 100, "trusted_compromise_assertion": True}, token="tok_ti_revoke").json()
    assert first["decision"] == "BLOCK"
    # Same token, no compromise hint this time: the learned revocation alone must block it.
    second = _post(tenant, {"amount": 100}, token="tok_ti_revoke").json()
    assert second["decision"] == "BLOCK"
    assert any(m["category"] == "revoked_token" for m in second["threat_intel"])
    # Revocations are tenant-scoped.
    other = _post(_tenant(), {"amount": 100}, token="tok_ti_revoke").json()
    assert other["decision"] == "ALLOW"


def test_compromise_origin_ip_is_learned_for_that_tenant_only():
    tenant = _tenant()
    _post(tenant, {"amount": 100, "trusted_compromise_assertion": True, "ip_address": "185.220.101.9"}, token="tok_a")
    later = _post(tenant, {"amount": 100, "ip_address": "185.220.101.9"}, token="tok_b").json()
    assert any(m["source"] == "netvrio-learned" for m in later["threat_intel"])
    other = _post(_tenant(), {"amount": 100, "ip_address": "185.220.101.9"}).json()
    assert other["threat_intel"] == []


# ── feed refresh ────────────────────────────────────────────────────────────────────────────

def test_refresh_is_fail_static(monkeypatch):
    monkeypatch.setenv("NETVRIO_TI_LIVE_FEEDS", "true")
    svc = ThreatIntelService(IndicatorStore())
    good = {"https://check.torproject.org/torbulkexitlist": "185.220.101.1\n185.220.101.2\n",
            "https://www.spamhaus.org/drop/drop_v4.json": '{"cidr":"45.95.0.0/16"}\n'}
    res = feeds.refresh_live_feeds(svc.store, fetcher=lambda url: good[url])
    assert res["tor-exit-nodes"] == 2 and res["spamhaus-drop"] == 1
    assert svc.assess("t", "e1", "45.95.3.3", None)[0].category == "hijacked_netblock"

    def broken(url):
        raise TimeoutError("feed down")

    res = feeds.refresh_live_feeds(svc.store, fetcher=broken)
    assert res["tor-exit-nodes"] == -1 and res["spamhaus-drop"] == -1
    # Previous indicators survive a failed refresh and the error is reported.
    assert svc.assess("t", "e2", "185.220.101.2", None)[0].source == "tor-exit-nodes"
    tor = next(s for s in svc.store.sources() if s["name"] == "tor-exit-nodes")
    assert "TimeoutError" in tor["last_error"]


def test_fetch_feed_refuses_plain_http():
    try:
        feeds.fetch_feed("http://example.com/list.txt")
    except ValueError as exc:
        assert "https" in str(exc)
    else:
        raise AssertionError("plain http must be refused")


# ── API ─────────────────────────────────────────────────────────────────────────────────────

def test_intel_status_and_matches_endpoints():
    tenant = _tenant()
    _post(tenant, {"amount": 100, "ip_address": "192.0.2.10"})
    status = client.get("/intel/status", params={"tenant": tenant}).json()
    assert any(s["name"] == "netvrio-synthetic" and s["indicators"] == 3 for s in status["sources"])
    items = client.get("/intel/matches", params={"tenant": tenant}).json()["items"]
    assert items[0]["matches"][0]["category"] == "carding_proxy"


def test_intel_refresh_requires_demo_mode(monkeypatch):
    monkeypatch.setenv("NETVRIO_DEMO_MODE", "false")
    assert client.post("/intel/refresh", params={"tenant": "t"}).status_code == 404


def test_rejected_payload_values_never_reach_telemetry():
    """Regression: pydantic tracebacks (with raw cvv / bearer values) were recorded on spans."""
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from backend.observability.tracing import add_span_processor

    exporter = InMemorySpanExporter()
    add_span_processor(SimpleSpanProcessor(exporter))
    tenant = _tenant()
    payload = {"event_id": f"evt_{uuid.uuid4().hex[:8]}", "merchant_id": tenant, "timestamp": int(time.time()),
               "data": {"amount": 1}, "cvv": "987", "nested": {"authorization": "Bearer LEAKCHECK_TOKEN"}}
    body = json.dumps(payload).encode()
    sig = hmac.new(b"dummy_webhook_secret", body, hashlib.sha256).hexdigest()
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": tenant})
    assert resp.status_code == 400
    spans = exporter.get_finished_spans()
    assert spans
    dump = json.dumps([[dict(e.attributes or {}) for e in s.events] + [dict(s.attributes or {})] for s in spans], default=str)
    assert "LEAKCHECK_TOKEN" not in dump and "987" not in dump
