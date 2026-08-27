# Razorpay Risk Manager Agent: Automated Testing & Validation

## 1. Test Suite Architecture

The system includes a comprehensive Pytest automated test suite covering unit, engine, security, policy, and end-to-end agentic workflows:

```
backend/tests/
├── test_security.py       # Luhn algorithm, HMAC fingerprinting, DLP redaction, injection sanitization
├── test_risk_engines.py   # Transaction risk, card risk, token risk, zombie token detection, scoring
├── test_policy.py         # Guardrail decision matrix (AUTO_EXECUTE, REVIEW_REQUIRED, NEVER_EXECUTE)
└── test_e2e_agent.py      # Golden Demo end-to-end investigation and risk drop (94 -> 21)
```

---

## 2. Test Execution & Results

```bash
# Run all tests
pytest -v
```

### Test Validation Results:
```text
backend/tests/test_e2e_agent.py::test_golden_demo_scenario_workflow PASSED      [  6%]
backend/tests/test_policy.py::test_policy_token_revocation_auto_execute PASSED  [ 13%]
backend/tests/test_policy.py::test_policy_token_revocation_zombie PASSED        [ 20%]
backend/tests/test_policy.py::test_policy_card_suspension_requires_approval PASSED [ 26%]
backend/tests/test_policy.py::test_policy_financial_transfer_strictly_prohibited PASSED [ 33%]
backend/tests/test_risk_engines.py::test_transaction_risk_high_anomaly PASSED   [ 40%]
backend/tests/test_risk_engines.py::test_transaction_risk_clean PASSED          [ 46%]
backend/tests/test_risk_engines.py::test_zombie_token_detection PASSED          [ 53%]
backend/tests/test_risk_engines.py::test_risk_scorer_weights_and_severity PASSED [ 60%]
backend/tests/test_security.py::test_luhn_algorithm_validation PASSED           [ 66%]
backend/tests/test_security.py::test_mask_pan PASSED                            [ 73%]
backend/tests/test_security.py::test_extract_bin PASSED                         [ 80%]
backend/tests/test_security.py::test_hmac_fingerprint_deterministic PASSED     [ 86%]
backend/tests/test_security.py::test_dlp_redaction PASSED                       [ 93%]
backend/tests/test_security.py::test_sanitize_untrusted_input PASSED            [100%]

======================= 15 passed in 1.43s =======================
```

---

## 3. Frontend Build Verification

```bash
cd frontend && npm run build
```
- Total transformed modules: 1,812
- Output: `dist/index.html`, `dist/assets/index.css`, `dist/assets/index.js`
- TypeScript errors: 0
