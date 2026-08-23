# Razorpay Risk Manager Agent: Comprehensive Gap Analysis & Engineering Roadmap

**Track**: Razorpay AI Risk Manager Track (AI Buildathon 2026)  
**Single Loss Class Focus**: *"Loss caused by compromised payment credentials being used in suspicious transactions."*

---

## 1. Current-State Audit

| Capability | Current State | Code Location | Status |
|---|---|---|---|
| **FastAPI Risk Gateway** | Operational with 10+ endpoints | `backend/app/main.py`, `backend/app/api/` | **Complete** |
| **Deterministic Risk Engines** | Amount/velocity/geo, card, token, zombie token | `backend/app/engines/` | **Complete** |
| **Risk Manager Agent** | 10-step Observe $\rightarrow$ Audit loop with 12 tools | `backend/app/agent/risk_agent.py` | **Complete** |
| **Policy Guardrails** | `AUTO_EXECUTE`, `REVIEW_REQUIRED`, `NEVER_EXECUTE` | `backend/app/engines/policy_engine.py` | **Complete** |
| **Action & Verification** | Gateway token revocation + vault query verification | `backend/app/engines/verification_engine.py` | **Complete** |
| **Tamper-Evident Hash Ledger**| SHA-256 hash chaining with `verify_chain_integrity` | `backend/app/engines/audit_ledger.py` | **Complete** |
| **Security & DLP** | HMAC-SHA-256 PAN fingerprinting, Luhn check, DLP scrubber | `backend/app/core/security.py` | **Complete** |
| **Razorpay Adapter** | `MockRazorpayAdapter` and `RazorpayTestAdapter` | `backend/app/integrations/razorpay_adapter.py`| **Complete** |
| **Automated Tests** | 21 passing pytest tests | `backend/tests/` | **Complete (21/21)** |
| **Frontend SOC Dashboard** | React 18 + Vite + Tailwind (0 TypeScript errors) | `frontend/src/` | **Complete** |

---

## 2. Gap Analysis Against Razorpay AI Risk Manager Track Requirements

| Requirement | Requirement from Hackathon | Current Gap | Remediation Plan |
|---|---|---|---|
| **1. Defined Class of Loss** | Clear scope definition on one loss class | Positioned broadly as multi-factor payment risk | Explicitly anchor on *"Loss from compromised payment credentials in suspicious transactions"* across all docs, UI, and evaluations |
| **2. Held-Out Evaluation Dataset** | Train / Val / Test split with synthetic records | Missing `evaluation/` dataset directory and generator | Build deterministic synthetic dataset generator creating 2,000 records ($70\%$ Train, $15\%$ Val, $15\%$ Test) with edge cases |
| **3. Measured Precision & Recall** | Measured performance on held-out test data | Only unit test assertions exist | Create `backend/app/evaluation/evaluator.py` to calculate Precision, Recall, F1, Accuracy, Specificity, FPR, FNR, and Confusion Matrix |
| **4. False-Positive Cost Analysis** | Expected business cost model with sensitivity analysis | Missing cost calculation | Implement $\text{Cost} = \text{FP} \times C_{\text{FP}} + \text{FN} \times C_{\text{FN}}$ with sensitivity sweeps in evaluation script |
| **5. Baseline & Ablation Study** | Rule-based baseline comparison & signal ablation | Missing ablation suite | Implement benchmark comparing simple heuristic rule vs. signal ablations vs. full Risk Manager |
| **6. Threshold Justification Curve**| Precision/Recall curve justifying the 75 threshold | Threshold 75 chosen by convention | Generate empirical Precision-Recall-F1-Cost curves over thresholds $20 - 90$ |
| **7. Agent Verification Benchmark**| Measured agent trajectory correctness over scenarios | Agent verified on 1 e2e test | Create 100-scenario automated agent benchmark testing tool selection, policy decisions, and verification rates |
| **8. Multi-Tenant IDOR Security** | Proof that Merchant A cannot access Merchant B data | Merchant ID stored but not strictly filtered across all queries | Add tenant-scoped queries and automated IDOR penetration tests in test suite |
| **9. Dashboard Evaluation Tab** | UI rendering confusion matrix, PR curves, and costs | Dashboard has 4 tabs (Timeline, Cards, Cases, Audit) | Add **Evaluation & Metrics** tab and **Live Risk Screening** table to React SOC dashboard |
| **10. Calibrated Reasoning** | Agent abstention/monitoring on weak/conflicting signals | Agent currently evaluates high anomaly scenarios | Add explicit calibrated reasoning when exposure confidence is low or transaction is domestic clean |

---

## 3. Evaluation Dataset Design (`evaluation/`)

- **Total Dataset Size**: 2,000 synthetic transaction records.
- **Split Ratio**:
  - `train.jsonl`: 1,400 records ($70\%$) - Used for threshold calibration
  - `validation.jsonl`: 300 records ($15\%$) - Used for hyperparameter tuning
  - `test.jsonl`: 300 records ($15\%$) - **Strictly Held-Out Evaluation Test Set**
- **Class Distribution**: $75\%$ Negative / Clean ($\text{Label} = 0$), $25\%$ Positive / Compromised ($\text{Label} = 1$).
- **Features**:
  - `transaction_id`: String (e.g. `eval_0001`)
  - `merchant_id`: String (e.g. `merchant_demo_01`)
  - `amount`: Float (₹)
  - `currency`: "INR"
  - `country`: 2-letter ISO code
  - `customer_country`: 2-letter ISO code
  - `velocity_10m`: Integer count of transactions in last 10 minutes
  - `card_fingerprint`: HMAC-SHA-256 string
  - `card_exposed`: Boolean
  - `exposure_confidence`: Float ($0.0 - 1.0$)
  - `exposure_source`: String (e.g. `RedLine_Stealer`, `PasteDump`, `None`)
  - `token_active`: Boolean
  - `token_age_days`: Integer
  - `is_zombie_token`: Boolean
  - `device_new`: Boolean
  - `failed_attempts_count`: Integer
  - `label`: Integer ($1 = \text{Compromised/Fraud Loss}, 0 = \text{Legitimate}$)
- **Edge Cases Covered**:
  1. Exposed card with clean domestic transaction (Weak signal $\rightarrow$ Label 0)
  2. High-value transaction on trusted device without exposure (Label 0)
  3. High velocity on newly created token with stealer log match (Label 1)
  4. Active zombie token on expired card with anomalous cross-border request (Label 1)
  5. Low-confidence exposure with normal velocity (Label 0)

---

## 4. Agent Evaluation Plan (`docs/AGENT_EVALUATION.md`)

Create an automated test harness executing 100 scenario permutations against `RiskManagerAgent`:
- **Investigation Completion Rate**: $\% $ of runs where agent completes the 10-step lifecycle without unhandled errors.
- **Tool Selection Accuracy**: $\% $ of steps where the appropriate tool was selected.
- **Policy Decision Accuracy**: $\% $ of steps where policy correctly blocked high-friction actions or allowed auto-execution.
- **Verification Success Rate**: $\% $ of remediated actions verified against the payment vault.
- **Target Benchmark**: $\ge 98\%$ agent trajectory accuracy.

---

## 5. Security & Multi-Tenancy Gaps

1. **Multi-Tenant Scoping**: Enforce `merchant_id` filtering in `get_transaction()`, `get_card()`, `get_token()`, `get_cases()`, and `get_audit_events()`.
2. **IDOR Test Suite**: Write explicit pytest suite verifying that Merchant A cannot access Merchant B resources.
3. **Prompt Injection & Sanitization**: Maintain schema-level data separation for untrusted CTI text.

---

## 6. UI & Dashboard Enhancements

1. **New Tab: Model Evaluation & Metrics**:
   - Confusion Matrix Card (TP, FP, TN, FN)
   - Performance Metrics: Precision, Recall, F1, Accuracy, Specificity, FPR, FNR
   - Baseline vs. Risk Manager comparative table
   - Expected Business Cost sensitivity display ($C_{\text{FP}} = ₹100, C_{\text{FN}} = ₹5,000$)
   - Threshold vs. Precision/Recall/Cost curve chart/table
2. **New Tab: Live Risk & Transactions Screening**:
   - Real-time transaction stream with risk score, severity badge, and 1-click Agent Investigate action.
3. **Updated Branding & Narrative**:
   - Explicitly highlight single loss class and defense-only architecture.

---

## 7. Exact Implementation Order

```
Step 1: Dataset Generation & Evaluation Module
  ├── evaluation/schema.json
  ├── evaluation/generate_dataset.py (Generates train/val/test jsonl files)
  ├── backend/app/evaluation/evaluator.py (Metrics, Baseline, Ablation, Threshold sweep)
  └── docs/DATASET.md & docs/MODEL_EVALUATION.md

Step 2: Multi-Tenant Scoping & Security Hardening
  ├── Enforce merchant_id in database models, queries, and APIs
  └── backend/tests/test_multi_tenancy.py (IDOR penetration tests)

Step 3: Agent Calibration & Contradictory Evidence
  ├── Calibrated reasoning in agent when exposure confidence is low
  ├── backend/tests/test_agent_evaluation.py (100-scenario harness)
  └── docs/AGENT_EVALUATION.md

Step 4: Expand Pytest Test Suite to 30+ Tests
  ├── test_evaluation_metrics.py
  ├── test_multi_tenancy.py
  ├── test_agent_calibration.py
  └── Verify 30+ tests passing

Step 5: Frontend Dashboard Enhancement
  ├── Add EvaluationTab.tsx (Confusion Matrix, Metrics, Baseline, Thresholds)
  ├── Add LiveRiskTable.tsx (Real-time transaction queue)
  ├── Update App.tsx and API client
  └── Verify npm run build (0 errors)

Step 6: Update Documentation & Demo Runbook
  ├── docs/DEMO_RUNBOOK.md
  ├── docs/FINAL_HACKATHON_AUDIT.md
  ├── Update README.md, HACKATHON_STORY.md, HACKATHON_DEMO.md, SECURITY.md, etc.
```
