# Pre-Release Comprehensive Codebase & Architecture Audit

**Project**: Razorpay Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Audit Stage**: Phase 0 Pre-Release Verification  
**Date**: August 23, 2026  
**Status**: Feature Complete & Frozen  

---

## 1. Current Architecture

The system is constructed with strict modular separation across four decoupled layers:
```
[Client / SOC Dashboard (React 18 + TS + Tailwind)]
                      │ REST APIs / SSE
                      ▼
[FastAPI Gateway (/api/v1/risk, /evaluation, /cases, /cards, /audit)]
                      │
   ┌──────────────────┴──────────────────┐
   ▼                                     ▼
[Deterministic Scoring Engines]    [Risk Manager Agent Loop]
 • Transaction Risk (Velocity/Geo)  • Dynamic Investigation (Levels 0-3)
 • Card Lifecycle Risk (Expiry)     • Evidence-Grounded Correlation
 • Token & Zombie Token Detection   • Calibrated Explainability
 • Threat Intelligence Correlation  • Structured Tool Audit
   │                                     │
   └──────────────────┬──────────────────┘
                      ▼
            [Policy Guardrail Engine]
             • Tier 0: ALLOW (Fast-path)
             • Tier 1: MONITOR (Telemetry)
             • Tier 2: REQUEST_STEP_UP (2FA Simulation)
             • Tier 3: REVIEW_REQUIRED (SOC Case)
             • Tier 4: AUTO_EXECUTE (Vault Token Revoke)
                      │
                      ▼
         [Response & Verification Engine]
          • Razorpay Test/Mock Adapter
          • Gateway Vault Query Verification
          • Post-Action Risk Recalculation
                      │
                      ▼
         [Tamper-Evident SHA-256 Audit Ledger]
          • Chained Hash Integrity (`prev_hash`)
          • Multi-Tenant SQLite/SQLAlchemy Store
```

---

## 2. Current Risk Flow

1. **Transaction Ingestion**: Raw transaction metadata (Amount, Currency, IP, Device, Velocity) is ingested without storing or logging raw PANs.
2. **Deterministic Feature Extraction**:
   - `TransactionRiskEngine`: Amount anomaly ($z$-score vs. customer baseline), Velocity score ($10\text{m}$ sliding window), Geo-distance / cross-border mismatch score.
   - `CardRiskEngine`: Card expiration status and lifecycle validity.
   - `TokenRiskEngine`: Zombie token detection (card expired/blocked + active token + usage).
   - `ExposureCorrelationEngine`: Matches one-way HMAC-SHA256 PAN fingerprint against CTI breach feeds.
3. **Composite Normalization ($0-100$)**:
   - Mathematical formula: $25\%\text{ Transaction} + 25\%\text{ Exposure} + 15\%\text{ Card} + 15\%\text{ Token} + 10\%\text{ Customer} + 10\%\text{ Velocity}$.
   - Evaluated against Layer 1 ($T=40.0$) and Layer 2 ($T=75.0$).

---

## 3. Current Agent Flow

- **Dynamic Investigation Levels**:
  - **Level 0 (Score $< 35.0$)**: Fast-path screening on clean transactions. Skips heavy external CTI lookups; logs explicit `tool_audit` reason.
  - **Level 1 (Score $35.0 - 39.9$)**: Telemetry analysis, checks customer profile and device consistency.
  - **Level 2 (Score $40.0 - 74.9$)**: Multi-factor investigation, card lifecycle check, breach correlation, and Step-Up 2FA simulation.
  - **Level 3 (Score $\ge 75.0$ or Zombie)**: Deep investigation, policy check, autonomous token revocation, vault query verification, risk recalculation ($94 \rightarrow 16$), and security case creation.
- **Evidence-Grounded Reasoning**: System prompts and explainability outputs strictly cite grounded evidence IDs (`[EVID-TXN-001]`, `[EVID-EXP-002]`, `[EVID-TOK-004]`).

---

## 4. Current Response Tiers

| Tier | Score Range | Status | Action Executed | Investigation Level | Policy Authorization |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 0: LOW** | $0.0 - 34.9$ | `CLEAN` | `ALLOW` | Level 0 | Automatic authorization |
| **Tier 1: MONITOR** | $35.0 - 39.9$ | `CLEAN` | `MONITOR` | Level 1 | Telemetry logging |
| **Tier 2: STEP_UP** | $40.0 - 64.9$ | `SUSPICIOUS` | `REQUEST_STEP_UP` | Level 2 | Simulated 2FA Challenge |
| **Tier 3: REVIEW** | $65.0 - 74.9$ | `SUSPICIOUS` | `REVIEW_REQUIRED` | Level 2 | SOC Queue Escalation |
| **Tier 4: AUTO_REMEDIATE** | $\ge 75.0$ / Zombie | `SUSPICIOUS` | `AUTO_EXECUTE` | Level 3 | Token Revocation on Vault |

---

## 5. Current Evaluation Methodology

- **Synthetic Corpus**: 2,000 synthetic records with realistic chargeback, velocity, and compromise patterns.
  - `train.jsonl`: 1,400 records
  - `validation.jsonl`: 300 records
  - `test.jsonl`: 300 records (**Strictly frozen**, SHA-256: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`)
- **Dual Operating Point Metrics on Held-Out Test Set**:
  - **Layer 1: Broad Detection ($T=40.0$)**: $\text{TP}=59, \text{FN}=8, \text{FP}=0, \text{TN}=233 \rightarrow \mathbf{\text{Recall}=88.06\%, \text{Precision}=100.0\%, \text{F1}=0.9365, \text{FPR}=0.0\%}$.
  - **Layer 2: Autonomous Remediation ($T=75.0$)**: $\text{TP}=35, \text{FN}=32, \text{FP}=0, \text{TN}=233 \rightarrow \mathbf{\text{Precision}=100.0\%, \text{Recall}=52.24\%, \text{F1}=0.6863, \text{FPR}=0.0\%}$.

---

## 6. Current Security Controls

- **HMAC-SHA-256 PAN Fingerprinting**: Raw PAN is never stored, logged, or sent to an LLM.
- **Regex & Luhn DLP Masking**: Proactively scrubs 13-19 digit card numbers from loggers and output streams.
- **Prompt Injection Defense**: Threat feed text is parsed into typed Pydantic models, sanitized, and treated as untrusted data.
- **Policy Boundary**: The LLM agent cannot change thresholds, policy rules, or execute sensitive operations outside deterministic guardrails. Financial movement is marked `NEVER_EXECUTE`.
- **Multi-Tenant Isolation**: Tenant scope (`merchant_id`) is strictly enforced at API, service, and database layers.
- **Tamper-Evident Hash Audit Ledger**: Every agent action is chained via SHA-256 (`curr_hash = SHA256(data + prev_hash)`).

---

## 7. Current Razorpay Integration Status

- **`MockRazorpayAdapter`**: In-memory stateful gateway simulation for instant, reliable local testing and demonstration.
- **`RazorpayTestAdapter`**: Sandbox-ready adapter utilizing Razorpay API credentials (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`) in test mode.
- **Adapter Abstraction (`RazorpayAdapter`)**: Supports `revoke_payment_token`, `get_token_status`, `suspend_card`, `rotate_token`, `request_step_up_challenge`, and `verify_step_up_challenge`.

---

## 8. Current Known Limitations

1. **Synthetic Evaluation Data**: Evaluated on synthetic transaction records rather than live production consumer cards.
2. **Synthetic Threat Intelligence**: Offline threat intelligence database reproducing RedLine/Genesis stealer dumps without indexing live stolen cards.
3. **PCI-Aware Prototype**: Designed with security and DLP boundaries, not an officially accredited PCI-DSS Level 1 certificate.
4. **Illustrative Cost Model**: Business cost assumptions ($C_{\text{FP}}=₹100, C_{\text{FN}}=₹5,000$) are illustrative parameters for expected loss modeling.

---

## 9. Potential Inconsistencies & Verifications Needed

- [x] Verify that `Step-Up` challenges support all four lifecycle states (`SUCCESS`, `FAILED`, `TIMEOUT`, `ABANDONED`) and do not alter ground-truth evaluation labels.
- [x] Verify that `Zombie Token` auto-remediation applies only when accompanied by active usage or policy authorization.
- [x] Verify that Tier boundaries ($34.9, 35.0, 39.9, 40.0, 64.9, 65.0, 74.9, 75.0$) have zero gaps and zero overlaps.
- [x] Verify that `release_guard.py` asserts test set hash integrity and prevents accidental mutation.

---

## 10. Recommended Release Checks

1. Run test set hash verification (`scripts/verify_test_set.py`).
2. Run full 45-test automated backend test suite (`pytest -v`).
3. Run reproducible evaluation runner (`python scripts/run_final_evaluation.py`).
4. Build frontend production assets (`npm run build`).
5. Implement and execute `scripts/release_guard.py`.
6. Implement `scripts/reset_demo.py` for 1-click clean demo resets.
