# Razorpay Risk Manager Agent: Hackathon Demo Walkthrough Guide

## 🎯 The Hackathon Golden Scenario

This guide outlines the exact 3-minute demonstration for judges and evaluators.

---

### Step 1: Start the Application

1. **Terminal 1 (Backend Gateway)**:
   ```bash
   uvicorn app.main:app --app-dir backend --reload --port 8000
   ```
2. **Terminal 2 (SOC Dashboard)**:
   ```bash
   cd frontend && npm run dev
   ```
3. Open `http://localhost:5173` in your browser.

---

### Step 2: Observe Initial SOC Metrics & Zombie Token Alert

When the dashboard loads, highlight:
- **Executive Metric Cards**: Monitored cards, tokens, and exposure counts.
- **Zombie Token Detection Panel**: Highlights token `tok_zombie_999` which is active on expired card `**** 8820` (Exp: 05/2024).
- **Cards Inventory**: Demonstrates zero raw PAN exposure (`**** **** **** 4921`) and zero-knowledge HMAC matching.

---

### Step 3: Trigger the Golden Attack Demo

Click the blue button: **"Execute Golden Attack Demo (₹18,500)"**.

### What Happens in Real Time:
1. **`OBSERVE` (14:01:00)**: Ingests transaction `TXN-2026-9042` for ₹18,500.
2. **`DETECT` (14:01:01)**:
   - Amount Anomaly: ₹18,500 vs. average ₹1,200 (+20 contribution)
   - Velocity Anomaly: 4 rapid attempts in 10 minutes (+14 contribution)
   - Geo Anomaly: Transaction originated in Moscow, Russia vs. customer home in Bengaluru, India (+15 contribution)
3. **`CORRELATE` (14:01:02)**: Agent matches HMAC fingerprint against `Telegram/RedLine-Stealer-Dump-08` (+25 contribution).
4. **`ASSESS RISK` (14:01:02)**: Multi-factor composite risk calculated as **94/100 (CRITICAL)**.
5. **`POLICY CHECK` (14:01:03)**:
   - `revoke_token`: Evaluated as `AUTO_EXECUTE` under Policy Rule `PR-01`.
   - `suspend_card`: Evaluated as `REVIEW_REQUIRED` (requires human approval).
6. **`ACT` (14:01:03)**: Agent invokes `revoke_payment_token("tok_test_123")` on Razorpay gateway.
7. **`VERIFY` (14:01:04)**: Queries Razorpay vault status API $\rightarrow$ confirmed `REVOKED`.
8. **`RECALCULATE` (14:01:04)**: Risk recalculated post-remediation $\rightarrow$ **Risk drops from 94 to 21 (LOW)**.
9. **`AUDIT` (14:01:05)**: Security Case `CASE-2026-XXXX` created and immutable audit log stored.

---

### Step 4: Inspect Generated Artifacts

1. **Agent Investigation Timeline**: Walk through the step-by-step chronological node cards.
2. **Security Cases Queue**: Switch to the **"Security Cases"** tab to see the auto-dispatched incident assigned to SOC Tier 2.
3. **Audit Trail**: Switch to the **"Audit Trail"** tab to inspect the cryptographic audit record.
4. **Reset State**: Click **"Reset State"** anytime to reset the test database for another demo run.
