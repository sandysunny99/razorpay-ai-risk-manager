import json
import os
import sys
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.evaluation.evaluator import ModelEvaluator

def run_error_analysis(split: str = "test.jsonl", threshold: float = 75.0) -> Dict[str, Any]:
    evaluator = ModelEvaluator()
    records = evaluator.load_dataset(split)
    
    false_negatives: List[Dict[str, Any]] = []
    false_positives: List[Dict[str, Any]] = []
    category_counts: Dict[str, int] = {}

    for r in records:
        score = evaluator.predict_record(r, model_type="full")
        true_label = r["label"]
        pred_label = 1 if score >= threshold else 0

        # False Negative: Actual Fraud/Compromise (1) but Model predicted Clean/Sub-critical (0)
        if true_label == 1 and pred_label == 0:
            # Classify the primary root cause category
            if not r.get("card_exposed", False):
                if r.get("velocity_10m", 1) <= 2 and r.get("amount", 0) <= 5000:
                    category = "Sub-critical velocity & amount without CTI exposure"
                else:
                    category = "Credential misuse without external CTI match"
            elif r.get("exposure_confidence", 0.0) < 0.60:
                category = "Low-confidence threat intelligence signal (< 0.60)"
            elif not r.get("token_active", False) and not r.get("is_zombie_token", False):
                category = "Exposed credential without active gateway token"
            elif r.get("country") == r.get("customer_country") and r.get("velocity_10m", 1) <= 2:
                category = "Domestic stealth anomaly (Normal velocity/Domestic IP)"
            else:
                category = "Sub-threshold multi-factor composite (Score 40-74)"

            category_counts[category] = category_counts.get(category, 0) + 1

            fn_entry = {
                "transaction_id": r["transaction_id"],
                "true_label": true_label,
                "predicted_label": pred_label,
                "risk_score": score,
                "threshold": threshold,
                "miss_category": category,
                "amount": r["amount"],
                "currency": r.get("currency", "INR"),
                "country": r.get("country"),
                "customer_country": r.get("customer_country"),
                "velocity_10m": r.get("velocity_10m"),
                "card_exposed": r.get("card_exposed"),
                "exposure_confidence": r.get("exposure_confidence"),
                "exposure_source": r.get("exposure_source"),
                "token_active": r.get("token_active"),
                "is_zombie_token": r.get("is_zombie_token"),
                "device_new": r.get("device_new"),
                "failed_attempts_count": r.get("failed_attempts_count", 0),
                "why_missed": f"Risk score ({score:.1f}) was below auto-response threshold ({threshold}). Root cause: {category}.",
                "what_would_catch_it": f"Lowering operating threshold to {score:.0f} or routing to Step-up 2FA Challenge (Review zone 50-74)."
            }
            false_negatives.append(fn_entry)

        # False Positive: Actual Clean (0) but Model predicted Fraud (1)
        elif true_label == 0 and pred_label == 1:
            false_positives.append({
                "transaction_id": r["transaction_id"],
                "true_label": true_label,
                "predicted_label": pred_label,
                "risk_score": score,
                "threshold": threshold,
                "amount": r["amount"],
                "country": r.get("country")
            })

    # Save to evaluation/false_negatives.jsonl
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../evaluation"))
    fn_path = os.path.join(out_dir, "false_negatives.jsonl")
    with open(fn_path, "w", encoding="utf-8") as f:
        for fn in false_negatives:
            f.write(json.dumps(fn) + "\n")

    return {
        "split": split,
        "threshold": threshold,
        "total_records": len(records),
        "total_positives": sum(1 for r in records if r["label"] == 1),
        "false_negative_count": len(false_negatives),
        "false_positive_count": len(false_positives),
        "miss_categories": category_counts,
        "fn_file_saved": fn_path
    }

if __name__ == "__main__":
    res = run_error_analysis("test.jsonl", 75.0)
    print(json.dumps(res, indent=2))
