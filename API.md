# Razorpay Risk Manager Agent: REST API Specification

Base URL: `http://localhost:8000/api/v1`  
Interactive OpenAPI Swagger Docs: `http://localhost:8000/docs`

---

## 1. Risk Management Endpoints

### `GET /risk/overview`
Returns high-level executive risk metrics.
```json
{
  "cards_monitored": 3,
  "tokens_monitored": 3,
  "active_zombie_tokens": 1,
  "high_risk_cards": 1,
  "critical_incidents": 1,
  "exposure_events_count": 2,
  "open_cases_count": 1,
  "system_status": "OPERATIONAL",
  "dry_run_mode": true
}
```

### `POST /risk/investigate`
Triggers full agentic investigation on a transaction.
- **Request Body**: `{"transaction_id": "TXN-2026-9042"}`
- **Response**: `InvestigationResponse` with initial vs. final risk, timeline steps, action taken, and factor breakdown.

---

## 2. Card Endpoints

### `GET /cards`
Lists all cards in the monitored vault with masked PANs and risk assessments.

---

## 3. Payment Token Endpoints

### `GET /tokens`
Lists all payment tokens with age, usage frequency, and status.

### `GET /tokens/zombies`
Scans and returns all active zombie tokens on dead cards.

### `POST /tokens/{token_id}/revoke`
Revokes a compromised payment token on the gateway.

---

## 4. Cases & Audit Endpoints

### `GET /cases`
Lists all open and resolved security cases.

### `GET /audit/events`
Returns the immutable security audit log.

---

## 5. Demo Controller Endpoints

### `GET /demo/scenarios`
Lists available testing scenarios (Golden Attack, Zombie Token Scan, Clean Benchmark).

### `POST /demo/trigger-golden-scenario`
Executes the full ₹18,500 hackathon attack simulation.

### `POST /demo/reset-data`
Resets the database to clean initial demo state.
