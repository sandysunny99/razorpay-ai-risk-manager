import sys
import os
import csv
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.evaluation.evaluator import ModelEvaluator

def run_validation_analysis():
    ev = ModelEvaluator()
    thresholds = [20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0]

    rows = []
    for th in thresholds:
        m = ev.evaluate_dataset("validation.jsonl", threshold=th, fp_cost=100.0, fn_cost=5000.0)
        cost_r10 = (m["fp"] * 100.0) + (m["fn"] * 1000.0)
        cost_r20 = (m["fp"] * 100.0) + (m["fn"] * 2000.0)
        cost_r30 = (m["fp"] * 100.0) + (m["fn"] * 3000.0)
        cost_r50 = (m["fp"] * 100.0) + (m["fn"] * 5000.0)
        cost_r100 = (m["fp"] * 100.0) + (m["fn"] * 10000.0)

        rows.append({
            "threshold": th,
            "tp": m["tp"],
            "fp": m["fp"],
            "tn": m["tn"],
            "fn": m["fn"],
            "precision": round(m["precision"], 4),
            "recall": round(m["recall"], 4),
            "f1": round(m["f1"], 4),
            "accuracy": round(m["accuracy"], 4),
            "fpr": round(m["fpr"], 4),
            "fnr": round(m["fnr"], 4),
            "expected_cost_r50": cost_r50,
            "expected_cost_r10": cost_r10,
            "expected_cost_r20": cost_r20,
            "expected_cost_r30": cost_r30,
            "expected_cost_r100": cost_r100
        })

    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../evaluation/validation_threshold_results.csv"))
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Saved validation threshold results to {csv_path}")
    print("\n" + "=" * 90)
    print("VALIDATION SET THRESHOLD EVALUATION (N = 300, Pos = 81, Neg = 219)")
    print("=" * 90)
    print(f"{'Threshold':<10} | {'TP':<4} | {'FP':<4} | {'TN':<4} | {'FN':<4} | {'Precision':<10} | {'Recall':<10} | {'F1':<8} | {'Cost (50x)':<14}")
    print("-" * 90)
    for r in rows:
        print(f"{r['threshold']:<10.1f} | {r['tp']:<4d} | {r['fp']:<4d} | {r['tn']:<4d} | {r['fn']:<4d} | {r['precision']*100:<9.2f}% | {r['recall']*100:<9.2f}% | {r['f1']:<8.4f} | INR {r['expected_cost_r50']:<12,.0f}")

    return rows

if __name__ == "__main__":
    run_validation_analysis()
