# Step-Up Verification Challenge & Risk Recalculation Flow

## 1. Overview & Business Rationale

When a transaction exhibits moderate behavioral friction (e.g., velocity spikes, untrusted device signatures, or moderate exposure signals) falling into **Tier 2 ($40.0 \le \text{Risk} < 65.0$)**, unilaterally revoking the user's saved card token or blocking checkout would introduce unwarranted customer drop-off. 

Instead of an immediate destructive action, the **Razorpay AI Risk Manager Agent** triggers a **Simulated Step-Up Verification Challenge (2FA/OTP)**.

```
       [ Incoming Transaction: Risk = 54.0 (Tier 2) ]
                             │
                             ▼
            [ Trigger Step-Up 2FA Challenge ]
              (SMS / In-App Notification)
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
    [ Challenge PASSED ]              [ Challenge FAILED ]
            │                                 │
   [ Risk Recalculated ]             [ Risk Escalated ]
   Velocity friction damped          Escalated to SOC Case
   Risk drops: 54.0 -> 27.0          Token quarantined / Revoked
   Status: APPROVED                  Status: BLOCKED / INVESTIGATE
```

---

## 2. API Endpoints & Interfaces

### 1. Initiate Step-Up Challenge
- **Endpoint**: `POST /api/v1/risk/step-up/request`
- **Request Body**:
  ```json
  {
    "transaction_id": "txn_2026_stepup_01",
    "challenge_method": "SMS_OTP_SIMULATION"
  }
  ```
- **Response Body**:
  ```json
  {
    "status": "CHALLENGE_ISSUED",
    "challenge_id": "ch_demo_134500_up_01",
    "transaction_id": "txn_2026_stepup_01",
    "challenge_method": "SMS_OTP_SIMULATION",
    "expires_at": "2026-08-23T08:05:00Z"
  }
  ```

### 2. Verify Step-Up Challenge & Recalculate Risk
- **Endpoint**: `POST /api/v1/risk/step-up/verify`
- **Request Body**:
  ```json
  {
    "challenge_id": "ch_demo_134500_up_01",
    "verification_code": "849201",
    "success": true
  }
  ```
- **Response Body**:
  ```json
  {
    "status": "CHALLENGE_VERIFIED_SUCCESSFUL",
    "challenge_id": "ch_demo_134500_up_01",
    "transaction_id": "txn_2026_stepup_01",
    "previous_risk": 54.0,
    "recalculated_risk": 27.0,
    "action": "STEP_UP_VERIFIED_ALLOW",
    "timestamp": "2026-08-23T08:00:22Z"
  }
  ```

---

## 3. Mathematical Recalculation Mechanics

When a cardholder successfully clears a 2FA step-up challenge:
1. **Behavioral Damping Factor ($D = 0.30$)**: The transaction velocity and device friction sub-score is damped by $70\%$ ($S_{\text{txn}} \leftarrow S_{\text{txn}} \times 0.30$).
2. **Exposure Persistence**: Threat intelligence exposure scores ($S_{\text{exp}}$) are preserved to retain audit visibility without triggering immediate token destruction.
3. **Composite Risk Drop**:
   $$R_{\text{final}} = \frac{0.30 \cdot S_{\text{txn}} W_{\text{txn}} + S_{\text{exp}} W_{\text{exp}} + S_{\text{crd}} W_{\text{crd}} + S_{\text{tok}} W_{\text{tok}} + S_{\text{cust}} W_{\text{cust}}}{\sum W}$$
   Typical transition: $54.0 \rightarrow 27.0$ ($\text{Tier 2: STEP\_UP} \rightarrow \text{Tier 0: LOW}$), allowing frictionless authorization.

---

## 4. Tamper-Evident Hash Audit

Every Step-Up lifecycle event is recorded to the cryptographically linked audit ledger:
- `event_id`: `AUD-STEPUP-8492`
- `actor`: `RiskManagerAgent`
- `action_requested`: `REQUEST_STEP_UP`
- `action_executed`: `STEP_UP_VERIFIED_ALLOW`
- `verification_result`: `CHALLENGE_VERIFIED_SUCCESSFUL`
- `current_hash`: `SHA256(previous_hash + payload)`
