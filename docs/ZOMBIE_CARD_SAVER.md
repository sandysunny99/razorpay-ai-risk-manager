# Zombie Card Saver: Intelligent Credential Lifecycle Detection & Selective Remediation

**Subsystem**: Zombie Card Saver Module  
**Package**: `backend/app/zombie_card_saver/`  
**Classification**: Enterprise Disruption-Prevention & Credential Lifecycle Intelligence  
**Authoritative Security Model**: Dual-Layer Architecture ($T_{\text{broad}} = 40.0$, $T_{\text{auto}} = 75.0$)

---

## 1. Problem Statement & Motivation

In modern card-on-file tokenization architectures (e.g. RBI Tokenization Mandate, Visa Token Service, Mastercard Digital Enablement Service), cards are tokenized across numerous merchant accounts. 

When a primary credit card reaches its end-of-life—due to expiration, bank re-issuance, administrative suspension, or theft/compromise—the underlying card state changes. However, **dependent tokens frequently remain ACTIVE** across merchant vaults.

### The Zombie Credential Dilemma
1. **Blind Revocation Hazard**: Revoking all tokens indiscriminately breaks legitimate active subscriptions (Netflix, AWS, SaaS bills), causing massive merchant disruption, churn, and severe customer friction.
2. **Zombie Token Exploitation**: Stale tokens on compromised or expired credentials can be hijacked or trigger silent recurring billing leakage without user oversight.

```
       +---------------------------------------------+
       |         Card Lifecycle State Change         |
       |     (EXPIRED / BLOCKED / REPLACED / SUSP)   |
       +---------------------------------------------+
                             |
                             v
       +---------------------------------------------+
       |        Zombie Card Saver Detection          |
       |  (Finds active dependent payment tokens)    |
       +---------------------------------------------+
                             |
                             v
       +---------------------------------------------+
       |   Multi-Vector Context & Impact Assessment  |
       |   • Token Usage Velocity                    |
       |   • Merchant Recurring Billing Dependency   |
       |   • CTI Breach Correlation (URLhaus/Paste)  |
       |   • Customer Friction & Disruption Index    |
       +---------------------------------------------+
                             |
                             v
       +---------------------------------------------+
       |      Selective Remediation Recommendation   |
       |   • HIGH RISK / EXPOSED  -> REVOKE TOKEN    |
       |   • RECURRING BILLING   -> REVIEW / DEFER   |
       |   • DORMANT / CLEAN     -> STEP-UP / MONITOR|
       +---------------------------------------------+
```

---

## 2. Core Architectural Components

### 2.1 Credential Detector (`detector.py`)
Evaluates card state against registered tokens to detect non-fraud lifecycle states:
- `HEALTHY`: Active card with active tokens.
- `AT_RISK`: Impending expiration ($\le 30$ days) or dormant active tokens.
- `ZOMBIE`: Card is `EXPIRED` or `REPLACED`, but 1 or more tokens remain `ACTIVE`.
- `CRITICAL`: Card is `BLOCKED` or exposed in threat feeds with active tokens.
- `RESOLVED`: All dependent tokens on inactive cards are safely remediated.

### 2.2 Severity Classifier (`severity.py`)
Classifies operational severity without treating standard card expiration as malicious fraud:
- `LOW`: Expired card with zero token velocity.
- `MEDIUM`: Expired card with active tokens and low velocity.
- `HIGH`: Velocity detected on zombie tokens or elevated composite risk.
- `CRITICAL`: Exposed credentials in external CTI feeds or parent card `BLOCKED`.

### 2.3 Merchant & Customer Impact Analyzer (`impact_analyzer.py`)
Calculates merchant revenue at risk and customer friction:
- Quantifies recurring subscriptions (e.g. utility bills, streaming services).
- Evaluates 30-day transaction volume on dependent tokens.
- Assesses customer friction score (`MINIMAL`, `LOW`, `MODERATE`, `HIGH`).

### 2.4 Selective Remediation Engine (`recommendation.py` & `service.py`)
Recommends fine-grained, non-disruptive actions:
1. `REVOKE_TOKEN`: Immediate cryptographic invalidation of high-risk or compromised tokens.
2. `REVIEW`: Flags recurring tokens for merchant renewal and customer notification.
3. `REQUEST_STEP_UP`: Challenges cardholder with step-up verification before allowing token renewal.
4. `MONITOR`: Retains safe tokens under active SOC observation.

---

## 3. REST API Specifications

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/zombie-cards` | Lists all detected zombie credentials with severity & metrics. |
| `GET` | `/api/v1/zombie-cards/statistics` | Retrieves aggregate metrics (tokens saved, tokens revoked, critical count). |
| `GET` | `/api/v1/zombie-cards/{card_id}/analysis` | Deep-dive token topology, merchant impact, and customer friction report. |
| `POST` | `/api/v1/zombie-cards/tokens/{token_id}/revoke` | Selectively revokes a target zombie token and appends SHA-256 audit block. |

---

## 4. Verification & Defense-in-Depth Guarantee

- **Zero Test Set Leakage**: Independent of the frozen benchmark test set ($N=300$, SHA-256 `76a26e7...`).
- **Cryptographic Auditability**: Every selective revocation is permanently recorded in the SHA-256 chained audit ledger (`audit_events`).
- **Gateway Idempotency**: Interacts safely with Razorpay Test Mode adapter with full mock/live toggle capability.
