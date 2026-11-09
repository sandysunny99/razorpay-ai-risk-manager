import json
import os
import secrets
import subprocess
import sys
import time
import uuid

import requests


def print_result(label, status):
    print(f"{label}: {status}")

def run_smoke_test():
    demo_secret = secrets.token_hex(32)
    env = dict(os.environ)
    env["NETVRIO_ENV"] = "test"
    env["NETVRIO_DEMO_MODE"] = "true"
    env["HMAC_SECRET_KEY"] = demo_secret

    backend_proc = subprocess.Popen(
        ["uvicorn", "backend.api.app:app", "--port", "8000"],
        cwd=os.getcwd(),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    try:
        # Readiness Polling
        ready = False
        start_time = time.time()
        while time.time() - start_time < 30:
            try:
                res = requests.get("http://localhost:8000/health/providers", timeout=2)
                if res.status_code == 200:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(0.5)

        if not ready:
            print_result("Backend startup", "FAIL")
            print("Reason: Failed to poll /health/providers within 30 seconds.")
            print("\nSMOKE_TEST_RESULT=FAIL\nEXIT CODE:\n1")
            sys.exit(1)
        print_result("Backend startup", "SUCCESS")
        print_result("Health", "PASS")

        def run_scenario(name, payload_data, tenant="tenant_123", sig_override=None):
            payload = {
                "event_id": f"evt_{name[0]}_{uuid.uuid4().hex[:8]}",
                "merchant_id": "tenant_123",
                "timestamp": int(time.time()),
                "data": payload_data
            }
            if "card_pan" in payload_data:
                payload["card_pan"] = payload_data.pop("card_pan")

            try:
                ds = requests.post("http://localhost:8000/webhooks/demo/sign", json=payload, timeout=5)
            except Exception as e:
                return 0, f"Demo Signer Exception: {str(e)}", None

            if ds.status_code != 200:
                return ds.status_code, f"Demo Signer Error {ds.status_code}", None

            ds_json = ds.json()
            raw_body = json.dumps(ds_json["payload"], separators=(',', ':')).encode('utf-8')
            sig = sig_override if sig_override else ds_json["signature"]

            headers = {"x-signature": sig, "x-tenant-id": tenant, "Content-Type": "application/json"}
            try:
                p = requests.post("http://localhost:8000/webhooks/payment", data=raw_body, headers=headers, timeout=10)
            except Exception as e:
                return 0, f"Webhook Exception: {str(e)}", None

            if p.status_code == 200:
                try:
                    audit_id = p.json().get("audit_id")
                    audit_resp = requests.get(f"http://localhost:8000/audit/{audit_id}", headers={"x-tenant-id": tenant}, timeout=5)
                    j = p.json()
                    return p.status_code, j, audit_resp
                except Exception as e:
                    return p.status_code, p.text, None
            return p.status_code, p.text, None

        # Verify Demo Signer and Webhook logic with scenario S
        code, j, audit = run_scenario("S", {"amount": 50})
        if code != 200:
            print_result("Demo Signer", "FAIL")
            print(f"Reason: HTTP {code}")
            print("\nSMOKE_TEST_RESULT=FAIL\nEXIT CODE:\n1")
            sys.exit(1)

        print_result("Demo Signer", "PASS")
        print_result("Webhook", "PASS")

        if audit and audit.status_code == 200:
            print_result("Audit", "PASS")
            if audit.json().get("chain_verified"):
                print_result("Chain", "PASS")
            else:
                print_result("Chain", "FAIL")
                print("Reason: chain_verified is False")
                print("\nSMOKE_TEST_RESULT=FAIL\nEXIT CODE:\n1")
                sys.exit(1)
        else:
            print_result("Audit", "FAIL")
            print("Reason: Could not fetch audit record")
            print("\nSMOKE_TEST_RESULT=FAIL\nEXIT CODE:\n1")
            sys.exit(1)

        print("")

        def assert_scenario(name, code, response_data, expected_code, expected_risk=None, expected_decision=None, expected_zombie=False):
            if code != expected_code:
                print(f"{name}: FAIL (Expected HTTP {expected_code}, got {code})")
                return False

            if expected_code == 200:
                actual_risk = response_data.get('risk_assessment', {}).get('risk_level')
                actual_dec = response_data.get('decision')

                if expected_risk and actual_risk != expected_risk:
                    print(f"{name}: FAIL (Expected risk {expected_risk}, got {actual_risk})")
                    return False
                if expected_decision and actual_dec != expected_decision:
                    print(f"{name}: FAIL (Expected decision {expected_decision}, got {actual_dec})")
                    return False

                if expected_zombie:
                    zom = response_data.get('zombie_signal')
                    if not zom:
                        print(f"{name}: FAIL (Missing zombie_signal)")
                        return False
                    if zom.get("severity") != "HIGH":
                        print(f"{name}: FAIL (Expected HIGH severity, got {zom.get('severity')})")
                        return False
                    if zom.get("recommendation") != "REQUIRE_STEP_UP":
                        print(f"{name}: FAIL (Expected REQUIRE_STEP_UP, got {zom.get('recommendation')})")
                        return False

            print(f"{name} -> PASS")
            return True

        passed = True

        # A
        c_a, r_a, _ = run_scenario("A", {"amount": 100})
        if not assert_scenario("A: LOW -> ALLOW", c_a, r_a, 200, "LOW", "ALLOW"):
            passed = False

        # B
        c_b, r_b, _ = run_scenario("B", {"amount": 15000})
        if not assert_scenario("B: MEDIUM -> REVIEW", c_b, r_b, 200, "MEDIUM", "REVIEW"):
            passed = False

        # C
        c_c, r_c, _ = run_scenario("C", {"amount": 120000})
        if not assert_scenario("C: HIGH -> BLOCK", c_c, r_c, 200, "HIGH", "BLOCK"):
            passed = False

        # D
        c_d, r_d, _ = run_scenario("D", {"amount": 100, "card_lifecycle": "EXPIRED", "recent_reuse_count": 6})
        if not assert_scenario("D: ZOMBIE -> REVIEW", c_d, r_d, 200, expected_decision="REVIEW", expected_zombie=True):
            passed = False

        print("")

        # E: Replay
        payload = {"event_id": f"evt_E_{uuid.uuid4().hex[:8]}", "merchant_id": "tenant_123", "timestamp": int(time.time()), "data": {"amount": 100}}
        ds = requests.post("http://localhost:8000/webhooks/demo/sign", json=payload, timeout=5)
        raw_body = json.dumps(ds.json()["payload"], separators=(',', ':')).encode('utf-8')
        h = {"x-signature": ds.json()["signature"], "x-tenant-id": "tenant_123", "Content-Type": "application/json"}
        requests.post("http://localhost:8000/webhooks/payment", data=raw_body, headers=h, timeout=10)
        p2 = requests.post("http://localhost:8000/webhooks/payment", data=raw_body, headers=h, timeout=10)
        if p2.status_code == 401:
            print("E: REPLAY -> 401 -> PASS")
        else:
            print(f"E: REPLAY -> 401 -> FAIL (Got {p2.status_code})")
            passed = False

        # F: Invalid HMAC
        c_f, _, _ = run_scenario("F", {"amount": 100}, sig_override="badsignature")
        if c_f == 401:
            print("F: INVALID HMAC -> 401 -> PASS")
        else:
            print(f"F: INVALID HMAC -> 401 -> FAIL (Got {c_f})")
            passed = False

        # G: Cross Tenant
        c_g, _, _ = run_scenario("G", {"amount": 100}, tenant="tenant_999")
        if c_g == 403:
            print("G: CROSS TENANT -> 403 -> PASS")
        else:
            print(f"G: CROSS TENANT -> 403 -> FAIL (Got {c_g})")
            passed = False

        # H: Sensitive Field
        c_h, _, _ = run_scenario("H", {"amount": 100, "card_pan": "SYNTHETIC_FORBIDDEN_FIELD"})
        if c_h == 422:
            print("H: SENSITIVE FIELD -> 422 -> PASS")
        else:
            print(f"H: SENSITIVE FIELD -> 422 -> FAIL (Got {c_h})")
            passed = False

        print("")
        if passed:
            print("FINAL: SMOKE TEST PASSED")
            print("SMOKE_TEST_RESULT=PASS")
            print("EXIT CODE:\n0")
            sys.exit(0)
        else:
            print("FINAL: SMOKE TEST FAILED")
            print("SMOKE_TEST_RESULT=FAIL")
            print("EXIT CODE:\n1")
            sys.exit(1)

    except Exception as e:
        print_result("Webhook", "FAIL")
        print(f"Reason: Exception occurred - {str(e)}")
        print("\nSMOKE_TEST_RESULT=FAIL\nEXIT CODE:\n1")
        sys.exit(1)
    finally:
        backend_proc.terminate()
        try:
            backend_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_proc.kill()
            backend_proc.wait()

if __name__ == "__main__":
    run_smoke_test()
