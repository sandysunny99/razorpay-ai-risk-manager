import csv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.engines.policy_engine import PolicyEngine
from app.evaluation.evaluator import ModelEvaluator


def run_policy_tier_validation():
    ev = ModelEvaluator()
    policy = PolicyEngine()
    records = ev.load_dataset("validation.jsonl")

    tier_counts = {"LOW": 0, "MONITOR": 0, "STEP_UP": 0, "REVIEW": 0, "AUTO_REMEDIATE": 0}
    action_counts = {}
    pos_by_tier = {"LOW": 0, "MONITOR": 0, "STEP_UP": 0, "REVIEW": 0, "AUTO_REMEDIATE": 0}
    neg_by_tier = {"LOW": 0, "MONITOR": 0, "STEP_UP": 0, "REVIEW": 0, "AUTO_REMEDIATE": 0}

    results = []

    for r in records:
        score = ev.predict_record(r, model_type="full")
        tier_info = policy.classify_risk_tier(score, context=r)

        tier = tier_info["response_tier"]
        action = tier_info["recommended_action"]
        label = r["label"]

        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        action_counts[action] = action_counts.get(action, 0) + 1

        if label == 1:
            pos_by_tier[tier] = pos_by_tier.get(tier, 0) + 1
        else:
            neg_by_tier[tier] = neg_by_tier.get(tier, 0) + 1

        results.append({
            "transaction_id": r["transaction_id"],
            "true_label": label,
            "risk_score": tier_info["risk_score"],
            "risk_level": tier_info["risk_level"],
            "detection_status": tier_info["detection_status"],
            "response_tier": tier,
            "policy_decision": tier_info["policy_decision"],
            "recommended_action": action,
            "amount": r.get("amount"),
            "velocity_10m": r.get("velocity_10m"),
            "card_exposed": r.get("card_exposed"),
            "token_active": r.get("token_active")
        })

    # Save to CSV
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../evaluation/validation_policy_results.csv"))
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"[OK] Saved validation policy results to {csv_path}")
    print("\n" + "=" * 80)
    print("VALIDATION SET RESPONSE TIER DISTRIBUTION (N = 300, Pos = 81, Neg = 219)")
    print("=" * 80)
    for tier, count in tier_counts.items():
        pct = (count / len(records)) * 100
        pos = pos_by_tier[tier]
        neg = neg_by_tier[tier]
        print(f"Tier: {tier:<16} | Total: {count:<4d} ({pct:5.1f}%) | Positives: {pos:<3d} | Negatives: {neg:<3d}")

    print("\n" + "-" * 80)
    print("RECOMMENDED ACTIONS DISTRIBUTION:")
    for action, count in action_counts.items():
        print(f"  - {action:<22}: {count:<4d} records")
    print("=" * 80)

    return {
        "tier_counts": tier_counts,
        "action_counts": action_counts,
        "pos_by_tier": pos_by_tier,
        "neg_by_tier": neg_by_tier
    }

if __name__ == "__main__":
    run_policy_tier_validation()
