# Tiered Defensive Response Policy Architecture & Validation

**Track**: Razorpay AI Risk Manager  
**Dataset Split**: `evaluation/validation.jsonl` ($N = 300$, Pos = 81, Neg = 219)  
**Configuration**: `RiskPolicyConfig` (`backend/app/engines/policy_engine.py`)  
**CSV Output**: `evaluation/validation_policy_results.csv`  

---

## 1. Multi-Tier Response Distribution (Validation Set, $N = 300$)

| Response Tier | Risk Range | Total Count | % of Traffic | Actual Positives | Actual Negatives | Primary Defensive Action |
|---|---|---|---|---|---|---|
| **Tier 0: LOW** | $0 \le \text{Risk} < 35$ | **219** | $73.0\%$ | 0 | 219 | **`ALLOW`** (Fast path authorization) |
| **Tier 1: MONITOR** | $35 \le \text{Risk} < 45$ | **7** | $2.3\%$ | 7 | 0 | **`MONITOR`** (Enhanced telemetry) |
| **Tier 2: STEP_UP** | $45 \le \text{Risk} < 65$ | **8** | $2.7\%$ | 8 | 0 | **`REQUEST_STEP_UP`** (Simulated 2FA challenge) |
| **Tier 3: REVIEW** | $65 \le \text{Risk} < 75$ | **0** | $0.0\%$ | 0 | 0 | **`SECURITY_REVIEW`** (Escalate to SOC case) |
| **Tier 4: AUTO_REMEDIATE** | $\text{Risk} \ge 75$ or Zombie | **66** | $22.0\%$ | 66 | 0 | **`REVOKE_TOKEN`** (Autonomous vault revocation) |
| **Total Corpus** | **$0 - 100$** | **300** | **$100.0\%$** | **81** | **219** | **$100.0\%$ Precision Guarantee** |

---

## 2. Distinction: Broad Detection vs. Autonomous Remediation

```
                  ┌─────────────────────────────────────────────────────────────┐
                  │                 TOTAL TRANSACTION INGRESS                   │
                  └──────────────────────────────┬──────────────────────────────┘
                                                 │
                                                 ▼
                  ┌─────────────────────────────────────────────────────────────┐
                  │         BROAD DETECTION LAYER (Threshold = 40.0)            │
                  │   • Intercepts 92.59% of compromised payment attacks       │
                  │   • Distinguishes CLEAN (Risk < 40) vs SUSPICIOUS (>= 40)   │
                  └──────────────────────────────┬──────────────────────────────┘
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
         ┌──────────────────────────────┐                 ┌──────────────────────────────┐
         │     TIER 2: STEP-UP 2FA      │                 │  TIER 4: AUTONOMOUS ACTION   │
         │     (Risk: 45.0 - 64.9)      │                 │     (Risk >= 75.0 / Zombie)  │
         │ • Simulated OTP / 2FA check  │                 │ • Auto-Revoke Razorpay Token │
         │ • Friction applied safely    │                 │ • Precision: 100.0% (0 FP)   │
         └──────────────────────────────┘                 └──────────────────────────────┘
```

---

## 3. Configurable Boundary Definition (`RiskPolicyConfig`)

```python
@dataclass
class RiskPolicyConfig:
    monitor_threshold: float = 35.0          # Tier 1: Light telemetry monitoring
    broad_detection_threshold: float = 40.0  # Layer 1: Broad detection boundary
    step_up_threshold: float = 45.0          # Tier 2: Step-Up verification challenge
    review_threshold: float = 65.0           # Tier 3: SOC human analyst sign-off
    auto_execute_threshold: float = 75.0     # Layer 2: Autonomous token destruction
    auto_revoke_token: bool = True           # Auto-revoke authorized on critical
    auto_suspend_card: bool = False          # Card suspension STRICTLY review-required
```
