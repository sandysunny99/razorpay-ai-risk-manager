# Live Hackathon Demo Runbook

**Hackathon**: Razorpay AI Buildathon 2026  
**Track**: AI Risk Manager  
**Project**: Razorpay Risk Manager Agent  

---

## 1. Quick Launch (Zero-Setup)

### Step A: Start the FastAPI Risk Gateway (Terminal 1)
```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
*Expected output: Application startup complete. Uvicorn running on `http://127.0.0.1:8000` (Docs: `http://127.0.0.1:8000/docs`).*

### Step B: Start the React SOC Dashboard (Terminal 2)
```powershell
cd frontend
npm run dev
```
*Expected output: Local: `http://localhost:5173/`.*

---

## 2. Live Demo Script (3-Minute Presentation Flow)

### Act 1: The Problem (30 seconds)
- **Point to the UI**: Open `http://localhost:5173`.
- **Narrative**:
  > *"Online businesses struggle with compromised payment credentials harvested from malware stealers and dark-web leaks. In 2026, static fraud rules either block legitimate users or miss stolen credentials when fraudsters use active saved payment tokens. Our AI Risk Manager autonomously monitors dark-web stealer dumps, correlates threat intelligence against card HMAC fingerprints, detects high-risk transactions, enforces strict policy guardrails, autonomously revokes vulnerable tokens on Razorpay Vault, and proves every decision in a tamper-evident audit ledger."*

### Act 2: Golden Attack Scenario (60 seconds)
- **Click**: Click the **"Scenario 1: Stealer Dump + Zombie Token (Golden Path)"** button.
- **Showcase the 10-Stage Agent Trajectory**:
  1. **OBSERVE**: Transaction `TXN-2026-9042` received ($₹18,500$ in Moscow, Russia).
  2. **DETECT**: Anomaly detected (Amount deviation + Cross-border IP + Velocity 4 attempts/10m).
  3. **INVESTIGATE & CORRELATE**: Card `**** **** **** 4921` matched in RedLine Stealer log ($96\%$ confidence).
  4. **REASON & ASSESS RISK**: Composite risk calculated at **$94/100$ (`CRITICAL`)**.
  5. **CHECK POLICY**: Policy Rule `PR-01` checked $\rightarrow$ Decision: `AUTO_EXECUTE` for token revocation; human approval required for card suspension.
  6. **ACT**: Agent calls `revoke_token(tok_test_123)` on Razorpay Vault adapter.
  7. **VERIFY & RECALCULATE**: Agent queries Razorpay API, verifies state is `REVOKED`, and recalculates composite risk score $\rightarrow$ **Risk drops from $94 \rightarrow 16$ (`LOW`)**.
  8. **AUDIT**: Incident recorded in Case `CASE-20260823-...` and hashed into the tamper-evident audit ledger.

### Act 3: Guardrail & Policy Denial Proof (30 seconds)
- **Click**: Click **"Scenario 2: Policy Denial (Card Suspension)"**.
- **Showcase**: The agent correctly denies autonomous card suspension because Policy Rule `PR-02` requires human approval ($Risk \ge 90$ with pending transactions).
- **Click**: Click **"Scenario 3: Prompt Injection Defense"**.
- **Showcase**: An adversarial prompt injected via merchant metadata is stripped by the DLP sanitizer and completely quarantined from LLM execution.

### Act 4: Empirical Model Evaluation & Live Risk Stream (30 seconds)
- **Click Tab**: **"Model Evaluation & Metrics"**.
- **Showcase**:
  - **Confusion Matrix on Held-Out Test Set ($N=300$)**: $TP=35, FP=0, TN=233, FN=32$.
  - **Precision**: **$100.0\%$** ($0$ False Positives on legitimate traffic).
  - **Ablation Study**: Incremental accuracy gains from Transaction only $\rightarrow$ Exposure $\rightarrow$ Token $\rightarrow$ Full Model.
  - **Cost Sensitivity**: Business cost calculated with illustrative $C_{\text{FP}}=₹100, C_{\text{FN}}=₹5,000$.
- **Click Tab**: **"Live Risk Screening Stream"**.
- **Showcase**: Real-time screening of transactions with 1-click Agent investigation.

### Act 5: Tamper-Evident Audit Ledger (30 seconds)
- **Click Tab**: **"Tamper-Evident Audit Trail"**.
- **Click**: Click **"Verify Hash Chain Integrity"**.
- **Showcase**: The SHA-256 chained hash ledger validates that $100\%$ of blocks are cryptographically intact ($Valid=True, Tampered=0$).

---

## 3. CLI Testing Runbook

To run all automated benchmarks and test suites:
```powershell
# Run all 31 unit, integration, policy, security, and benchmark tests
pytest -v

# Run held-out evaluation benchmark directly
python -c "from app.evaluation.evaluator import ModelEvaluator; ev = ModelEvaluator(); print(ev.evaluate_dataset('test.jsonl'))"

# Verify Frontend TypeScript & Production Build
cd frontend
npm run build
```
