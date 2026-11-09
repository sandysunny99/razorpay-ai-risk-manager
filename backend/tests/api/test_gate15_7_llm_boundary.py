import time
import uuid

from fastapi.testclient import TestClient
import pytest

from backend.api.app import app
import backend.api.routes.webhooks
from backend.llm.schemas import RiskLLMResponse
from backend.tests.api.test_gate15_demo_security import sign_payload

client = TestClient(app)

@pytest.mark.parametrize("amount, mock_action, expected_decision", [
    (120000.0, "ALLOW", "BLOCK"),    # TEST A: Deterministic HIGH (amount 120000 -> block), LLM ALLOW
    (15000.0, "BLOCK", "REVIEW"),    # TEST B: Deterministic MEDIUM (amount 15000 -> review), LLM BLOCK
    (100.0, "BLOCK", "ALLOW"),       # TEST C: Deterministic LOW (amount 100 -> allow), LLM BLOCK
])
def test_webhook_llm_boundary_does_not_override(amount, mock_action, expected_decision, monkeypatch):
    def fake_analyze(*args, **kwargs):
        resp = RiskLLMResponse(
            status="SUCCESS",
            recommended_action=mock_action,
            confidence=99,
            explanation="Mock explanation",
            cited_evidence_ids=[]
        )
        return resp, {"provider": "MockProvider", "status": "SUCCESS"}

    monkeypatch.setattr("backend.api.routes.webhooks.llm_router.analyze", fake_analyze)
    monkeypatch.setattr("backend.api.routes.webhooks.validate_llm_advisory", lambda adv, valid_ids: adv)

    payload = {
        "event_id": f"bound_{str(uuid.uuid4())[:8]}",
        "timestamp": int(time.time()),
        "merchant_id": "tenant_123",
        "data": {"amount": amount, "currency": "USD"}
    }
    body, sig = sign_payload(payload)

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "tenant_123"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision"] == expected_decision
    assert data["ai_advisory"]["recommended_action"] == mock_action

def test_all_providers_fail_real_webhook(monkeypatch):
    monkeypatch.setattr("backend.api.routes.webhooks.llm_router.analyze",
        lambda *args, **kwargs: (None, {"provider": "UNAVAILABLE", "status": "FAILED", "failure_reason": "ALL_UNAVAILABLE"}))

    payload = {
        "event_id": f"fail_{str(uuid.uuid4())[:8]}",
        "timestamp": int(time.time()),
        "merchant_id": "tenant_123",
        "data": {"amount": 5.0} # Low -> ALLOW
    }
    body, sig = sign_payload(payload)

    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "tenant_123"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision"] == "ALLOW"
    assert data["ai_advisory"]["recommended_action"] == "UNAVAILABLE"
    assert data["ai_advisory"]["provider"] == "UNAVAILABLE"
    assert "audit_id" in data

def test_strong_tenant_isolation(monkeypatch):
    from backend.security.tenant import get_current_tenant

    # 1. Tenant A Request
    captured_tenant_A = []
    def fake_analyze_A(*args, **kwargs):
        captured_tenant_A.append(get_current_tenant())
        return None, {"provider": "MockA"}

    monkeypatch.setattr("backend.api.routes.webhooks.llm_router.analyze", fake_analyze_A)

    payload_A = {
        "event_id": f"tenant_A_{str(uuid.uuid4())[:8]}",
        "timestamp": int(time.time()),
        "merchant_id": "tenant_A",
        "data": {"amount": 5.0}
    }
    body_A, sig_A = sign_payload(payload_A)
    resp_A = client.post("/webhooks/payment", content=body_A, headers={"x-signature": sig_A, "x-tenant-id": "tenant_A"})
    assert resp_A.status_code == 200
    assert captured_tenant_A[0] == "tenant_A"
    audit_id_A = resp_A.json()["audit_id"]
    evidence_id_A = resp_A.json()["evidence_ids"][0]

    # 2. Tenant B Request
    captured_tenant_B = []
    def fake_analyze_B(*args, **kwargs):
        captured_tenant_B.append(get_current_tenant())
        return None, {"provider": "MockB"}

    monkeypatch.setattr("backend.api.routes.webhooks.llm_router.analyze", fake_analyze_B)

    payload_B = {
        "event_id": f"tenant_B_{str(uuid.uuid4())[:8]}",
        "timestamp": int(time.time()),
        "merchant_id": "tenant_B",
        "data": {"amount": 10.0}
    }
    body_B, sig_B = sign_payload(payload_B)
    resp_B = client.post("/webhooks/payment", content=body_B, headers={"x-signature": sig_B, "x-tenant-id": "tenant_B"})
    assert resp_B.status_code == 200
    assert captured_tenant_B[0] == "tenant_B"
    audit_id_B = resp_B.json()["audit_id"]

    # 3. Tenant A cannot retrieve Tenant B audit data
    audit_fetch_1 = client.get(f"/audit/{audit_id_B}", headers={"x-tenant-id": "tenant_A"})
    # Architecture intentionally uses 404 instead of 403 to prevent resource enumeration.
    assert audit_fetch_1.status_code == 404
    assert "Audit not found or access denied" in audit_fetch_1.text
    assert "decision" not in audit_fetch_1.text  # No protected data returned

    # 4. Tenant B cannot retrieve Tenant A audit data
    audit_fetch_2 = client.get(f"/audit/{audit_id_A}", headers={"x-tenant-id": "tenant_B"})
    # Architecture intentionally uses 404 instead of 403 to prevent resource enumeration.
    assert audit_fetch_2.status_code == 404
    assert "Audit not found or access denied" in audit_fetch_2.text
    assert "decision" not in audit_fetch_2.text  # No protected data returned

    # 5. Tenant A evidence IDs are not accepted as Tenant B evidence
    # We don't patch validate_llm_advisory! We let it run.
    def fake_analyze_B_evidence(*args, **kwargs):
        # Malicious LLM tries to cite Tenant A's evidence
        resp = RiskLLMResponse(status="SUCCESS", recommended_action="BLOCK", confidence=99, explanation="e", cited_evidence_ids=[evidence_id_A])
        return resp, {"provider": "MockB"}

    monkeypatch.setattr("backend.api.routes.webhooks.llm_router.analyze", fake_analyze_B_evidence)

    payload_B2 = {
        "event_id": f"tenant_B2_{str(uuid.uuid4())[:8]}",
        "timestamp": int(time.time()),
        "merchant_id": "tenant_B",
        "data": {"amount": 15.0}
    }
    body_B2, sig_B2 = sign_payload(payload_B2)
    resp_B2 = client.post("/webhooks/payment", content=body_B2, headers={"x-signature": sig_B2, "x-tenant-id": "tenant_B"})
    assert resp_B2.status_code == 200
    # Because evidence ID is invalid for Tenant B, advisory is rejected (UNAVAILABLE)
    assert resp_B2.json()["ai_advisory"]["recommended_action"] == "UNAVAILABLE"

def test_evidence_id_validation_real_package(monkeypatch):
    # Do NOT patch validate_llm_advisory. Let the real one run.

    # 1. Unknown Evidence ID -> Rejected
    def fake_analyze_unknown(*args, **kwargs):
        # Return a response citing a totally fake evidence ID
        resp = RiskLLMResponse(status="SUCCESS", recommended_action="BLOCK", confidence=99, explanation="e", cited_evidence_ids=["fake_id_123"])
        return resp, {"provider": "Mock"}

    monkeypatch.setattr("backend.api.routes.webhooks.llm_router.analyze", fake_analyze_unknown)

    payload = {
        "event_id": f"evid_{str(uuid.uuid4())[:8]}",
        "timestamp": int(time.time()),
        "merchant_id": "tenant_123",
        "data": {"amount": 5.0}
    }
    body, sig = sign_payload(payload)
    resp = client.post("/webhooks/payment", content=body, headers={"x-signature": sig, "x-tenant-id": "tenant_123"})
    assert resp.status_code == 200
    # Because of hallucinated evidence ID, advisory is stripped and marked UNAVAILABLE
    assert resp.json()["ai_advisory"]["recommended_action"] == "UNAVAILABLE"

    # 2. Valid Evidence ID -> Accepted
    def fake_analyze_valid(*args, **kwargs):
        req = args[0] if len(args) > 0 else kwargs.get('request')
        # Use the real evidence_id assigned by the EvidenceBuilder
        resp = RiskLLMResponse(status="SUCCESS", recommended_action="BLOCK", confidence=99, explanation="e", cited_evidence_ids=[req.evidence_package_id])
        return resp, {"provider": "Mock"}

    monkeypatch.setattr("backend.api.routes.webhooks.llm_router.analyze", fake_analyze_valid)

    payload2 = {
        "event_id": f"evid_{str(uuid.uuid4())[:8]}",
        "timestamp": int(time.time()),
        "merchant_id": "tenant_123",
        "data": {"amount": 5.0}
    }
    body2, sig2 = sign_payload(payload2)
    resp2 = client.post("/webhooks/payment", content=body2, headers={"x-signature": sig2, "x-tenant-id": "tenant_123"})
    assert resp2.status_code == 200
    assert resp2.json()["ai_advisory"]["recommended_action"] == "BLOCK"
