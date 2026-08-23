# Dataset Integrity & Split Audit Report

**Track**: Razorpay AI Risk Manager  
**Dataset Path**: `evaluation/` (`train.jsonl`, `validation.jsonl`, `test.jsonl`)  
**Generation Script**: `evaluation/generate_dataset.py` (`SEED = 42`)  
**Schema Definition**: `evaluation/schema.json`  

---

## 1. Split Sizes & Overlap Verification

| Dataset Split | Total Records | Unique IDs | Overlap with Test | Overlap with Train | Overlap with Validation | Status |
|---|---|---|---|---|---|---|
| **`train.jsonl`** | 1,400 | 1,400 | **0 records (0.0%)** | N/A | **0 records (0.0%)** | **CLEAN & ISOLATED** |
| **`validation.jsonl`** | 300 | 300 | **0 records (0.0%)** | **0 records (0.0%)** | N/A | **CLEAN & ISOLATED** |
| **`test.jsonl` (Held-Out)**| 300 | 300 | N/A | **0 records (0.0%)** | **0 records (0.0%)** | **STRICTLY HELD-OUT** |

- **ID Uniqueness**: $100\%$ unique IDs across all 2,000 generated records.
- **Data & Label Leakage**: **Zero partition overlap**. All evaluations on `test.jsonl` are completely out-of-sample.

---

## 2. Class Distribution Across Partitions

| Partition | Negative (Clean = 0) | Positive (Compromised = 1) | Positive Ratio | Class Balance Profile |
|---|---|---|---|---|
| **Training Set** | 1,048 ($74.86\%$) | 352 ($25.14\%$) | $25.14\%$ | Realistic Payment Risk Imbalance |
| **Validation Set** | 219 ($73.00\%$) | 81 ($27.00\%$) | $27.00\%$ | Realistic Payment Risk Imbalance |
| **Held-Out Test Set** | 233 ($77.67\%$) | 67 ($22.33\%$) | $22.33\%$ | Realistic Payment Risk Imbalance |

---

## 3. Cryptographic Partition Hashes

| File | SHA-256 Checksum | Immutability Status |
|---|---|---|
| `evaluation/test.jsonl` | `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f` | **FROZEN & VERIFIED** |
| `evaluation/validation.jsonl` | `e7ad48163c6a3b3d0937aa2ccd4e71dd00d6bd38f87d82508bb258b01649f361` | **FROZEN & VERIFIED** |
| `evaluation/train.jsonl` | `34f38920a046e1b7e1d6c1634c619a7433bd22e2fc0dacb3fee65e80703231f5` | **FROZEN & VERIFIED** |

---

## 4. Feature Schema & Edge Case Validation

All 2,000 records strictly conform to [evaluation/schema.json](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/evaluation/schema.json):
1. **Hard Negatives (Legitimate with Friction Signals)**:
   - High amount (> ₹10,000) on trusted device in domestic geography with zero breach exposure ($\text{Label} = 0$).
   - New device login on small amount (₹400) without breach exposure ($\text{Label} = 0$).
   - Legitimate cross-border corporate traveller on trusted corporate card ($\text{Label} = 0$).
   - Low-confidence exposure (< 0.40) from stale paste dump with normal payment velocity ($\text{Label} = 0$).
2. **Hard Positives (Compromised Credentials with Sub-Critical Signals)**:
   - Moderate velocity anomaly (2-3 attempts) + new device + active token without prominent amount spike ($\text{Label} = 1$).
   - Active zombie token on expired card with subtle cross-border velocity ($\text{Label} = 1$).
   - RedLine Stealer match with active token during night-time hours ($\text{Label} = 1$).
