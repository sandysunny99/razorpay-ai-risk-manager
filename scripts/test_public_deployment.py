import argparse
import hashlib
import hmac
import json
import sys
import time

import httpx


def test_public_deployment(base_url: str, secret: str = "rzp_test_mock_agent_secret"):
    base_url = base_url.rstrip("/")
    print("=" * 70)
    print(f"TESTING LIVE PUBLIC DEPLOYMENT: {base_url}")
    print("=" * 70)

    all_passed = True
    with httpx.Client(base_url=base_url, timeout=15.0, follow_redirects=True) as client:
        # 1. Health Probe
        try:
            res = client.get("/health")
            if res.status_code == 200:
                print(f"[PASS] GET /health                             -> HTTP 200 (Status: {res.json().get('status')})")
            else:
                print(f"[FAIL] GET /health                             -> HTTP {res.status_code}")
                all_passed = False
        except Exception as e:
            print(f"[ERROR] GET /health                             -> {e}")
            all_passed = False

        # 2. Dependency Health Probe
        try:
            res = client.get("/api/v1/health/dependencies")
            if res.status_code == 200:
                print("[PASS] GET /api/v1/health/dependencies         -> HTTP 200")
            else:
                print(f"[FAIL] GET /api/v1/health/dependencies         -> HTTP {res.status_code}")
                all_passed = False
        except Exception as e:
            print(f"[ERROR] GET /api/v1/health/dependencies         -> {e}")
            all_passed = False

        # 3. Zombie Card Saver API
        try:
            res = client.get("/api/v1/zombie-cards")
            if res.status_code == 200:
                cards = res.json()
                print(f"[PASS] GET /api/v1/zombie-cards                -> HTTP 200 ({len(cards)} zombie cards detected)")
            else:
                print(f"[FAIL] GET /api/v1/zombie-cards                -> HTTP {res.status_code}")
                all_passed = False
        except Exception as e:
            print(f"[ERROR] GET /api/v1/zombie-cards                -> {e}")
            all_passed = False

        # 4. Security & Data Protection Matrix
        try:
            res = client.get("/api/v1/security/data-protection")
            if res.status_code == 200:
                print(f"[PASS] GET /api/v1/security/data-protection     -> HTTP 200 (Security Status: {res.json().get('status')})")
            else:
                print(f"[FAIL] GET /api/v1/security/data-protection     -> HTTP {res.status_code}")
                all_passed = False
        except Exception as e:
            print(f"[ERROR] GET /api/v1/security/data-protection     -> {e}")
            all_passed = False

        # 5. Webhook Security Verification
        try:
            payload = {
                "event": "payment.authorized",
                "account_id": "acc_pub_01",
                "event_id": f"evt_pub_{int(time.time()*1000)}",
                "payload": {"payment": {"entity": {"id": f"pay_pub_{int(time.time())}", "amount": 100000, "status": "authorized"}}}
            }
            body_bytes = json.dumps(payload).encode("utf-8")
            sig = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

            # Missing signature check
            res_unsig = client.post("/api/v1/webhooks/razorpay", content=body_bytes, headers={"Content-Type": "application/json"})
            if res_unsig.status_code == 401:
                print("[PASS] POST /api/v1/webhooks/razorpay (Unsigned) -> HTTP 401 (Correctly Rejected)")
            else:
                print(f"[FAIL] POST /api/v1/webhooks/razorpay (Unsigned) -> HTTP {res_unsig.status_code} (Expected 401)")
                all_passed = False

            # Signed valid check
            res_sig = client.post("/api/v1/webhooks/razorpay", content=body_bytes, headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig, "X-Razorpay-Event-Id": payload["event_id"]})
            if res_sig.status_code == 200:
                print(f"[PASS] POST /api/v1/webhooks/razorpay (Signed)   -> HTTP 200 (Ingested Event: {res_sig.json().get('event_id')})")
            else:
                print(f"[FAIL] POST /api/v1/webhooks/razorpay (Signed)   -> HTTP {res_sig.status_code}")
                all_passed = False
        except Exception as e:
            print(f"[ERROR] Webhook verification                    -> {e}")
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("[SUCCESS] ALL PUBLIC DEPLOYMENT ENDPOINTS VERIFIED & OPERATIONAL.")
        sys.exit(0)
    else:
        print("[FAILURE] ONE OR MORE PUBLIC ENDPOINTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify public Razorpay Risk Manager deployment")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of deployed service")
    parser.add_argument("--secret", default="rzp_test_mock_agent_secret", help="Razorpay webhook secret")
    args = parser.parse_args()
    test_public_deployment(args.url, args.secret)
