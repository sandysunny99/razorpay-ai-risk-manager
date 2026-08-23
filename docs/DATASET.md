# Evaluation Dataset Specification & Held-Out Test Methodology

**Target Loss Class**: *"Loss caused by compromised payment credentials being used in suspicious transactions."*  
**Generator Seed**: `SEED=42`  
**Total Records**: 2,000 synthetic transactions  
**Schema Definition**: [`evaluation/schema.json`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/evaluation/schema.json)

---

## 1. Dataset Partition & Class Distribution

| Partition | File | Total Records | Positive (Fraud / Compromised) | Negative (Clean / Legitimate) | Class Balance | Purpose |
|---|---|---|---|---|---|---|
| **Training** | `evaluation/train.jsonl` | **1,400** | 352 | 1,048 | 25.1% Pos / 74.9% Neg | Initial threshold exploration |
| **Validation** | `evaluation/validation.jsonl` | **300** | 81 | 219 | 27.0% Pos / 73.0% Neg | Hyperparameter tuning |
| **Held-Out Test** | `evaluation/test.jsonl` | **300** | 67 | 233 | 22.3% Pos / 77.7% Neg | **Strictly held-out final benchmark** |
| **Total** | | **2,000** | **500** | **1,500** | **25.0% Pos / 75.0% Neg** | Complete evaluation corpus |

---

## 2. Feature Definitions & Semantic Types

| Feature Field | Type | Description |
|---|---|---|
| `transaction_id` | String | Unique transaction reference (e.g. `eval_0001`) |
| `merchant_id` | String | Merchant entity ID for multi-tenant isolation |
| `amount` | Float | Transaction amount in INR (₹) |
| `country` | String | ISO 2-letter origin IP country |
| `customer_country` | String | Customer's registered home country |
| `velocity_10m` | Integer | Transaction attempts in preceding 10-minute window |
| `card_exposed` | Boolean | Threat intelligence breach match indicator |
| `exposure_confidence` | Float | Match confidence ($0.0 - 1.0$) from CTI provider |
| `exposure_source` | String | Threat dump source name (e.g. `RedLine_Stealer_Dump`) |
| `token_active` | Boolean | Whether an active vault token exists |
| `token_age_days` | Integer | Age of payment token in days |
| `is_zombie_token` | Boolean | Token active on expired/blocked card |
| `card_expired` | Boolean | Physical card expiration status |
| `device_new` | Boolean | Unrecognized device fingerprint |
| `failed_attempts_count` | Integer | Recent 24h authorization failure count |
| `label` | Integer | Ground truth ($1 = \text{Compromised Loss}, 0 = \text{Legitimate}$) |

---

## 3. Strict Held-Out Test Set Isolation Rule

> [!IMPORTANT]
> To prevent data leakage and guarantee scientific validity:
> - The test set (`test.jsonl`) is NEVER used during threshold tuning or heuristic parameter optimization.
> - The test set is only evaluated during the final evaluation phase.
