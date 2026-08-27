import json
import os
from typing import Any, Dict, List, Optional

from app.engines.risk_scorer import RiskScoringEngine


class ModelEvaluator:
    """
    Evaluator for measuring risk detection performance on held-out datasets.
    Calculates Precision, Recall, F1, Confusion Matrix, Expected Cost,
    Baseline Comparison, and Ablation Study.
    """

    DEFAULT_FP_COST = 100.0   # Illustrative cost of customer friction / review (INR)
    DEFAULT_FN_COST = 5000.0  # Illustrative cost of fraud loss from compromised credential (INR)

    def __init__(self, dataset_dir: Optional[str] = None):
        if dataset_dir:
            self.dataset_dir = dataset_dir
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "evaluation"))
            self.dataset_dir = base_dir

        self.risk_scorer = RiskScoringEngine()

    def load_dataset(self, split: str = "test.jsonl") -> List[Dict[str, Any]]:
        path = os.path.join(self.dataset_dir, split)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Evaluation dataset file not found at: {path}")

        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records

    def predict_record(self, record: Dict[str, Any], model_type: str = "full") -> float:
        """
        Computes composite risk score (0 - 100) for a record based on model type.
        """
        # 1. Transaction Risk
        txn_score = 0.0
        if record["amount"] > 10000:
            txn_score += min(35.0, (record["amount"] / 1000.0) * 1.5)
        if record["velocity_10m"] > 1:
            txn_score += min(35.0, (record["velocity_10m"] - 1) * 8.0)
        if record["country"] != record["customer_country"]:
            txn_score += 25.0
        if record.get("device_new", False):
            txn_score += 15.0
        txn_score = min(100.0, txn_score)

        # 2. Exposure Risk
        exp_score = 0.0
        if record["card_exposed"]:
            exp_score = record["exposure_confidence"] * 100.0

        # 3. Card Risk
        card_score = 0.0
        if record.get("card_expired", False):
            card_score += 60.0
        if record.get("failed_attempts_count", 0) > 0:
            card_score += min(40.0, record["failed_attempts_count"] * 10.0)
        card_score = min(100.0, card_score)

        # 4. Token Risk
        tok_score = 0.0
        if record.get("is_zombie_token", False):
            tok_score = 90.0
        elif record.get("token_active", False):
            tok_score = 80.0 if (record["card_exposed"] and record["exposure_confidence"] >= 0.7) else 30.0

        if model_type == "txn_only":
            return txn_score
        elif model_type == "txn_exposure":
            return min(100.0, (txn_score * 0.5) + (exp_score * 0.5))
        elif model_type == "txn_exposure_token":
            return min(100.0, (txn_score * 0.4) + (exp_score * 0.4) + (tok_score * 0.2))
        elif model_type == "baseline_rule":
            # Heuristic baseline: flags positive if any single heuristic fires
            is_suspicious = (
                (record["card_exposed"] and record["exposure_confidence"] >= 0.5) or
                record["velocity_10m"] >= 3 or
                record["country"] != record["customer_country"] or
                record.get("is_zombie_token", False)
            )
            return 85.0 if is_suspicious else 10.0

        # Full Model (Weight: 25 Txn, 25 Exp, 15 Card, 15 Tok, 10 Cust, 10 Merch)
        res = self.risk_scorer.calculate(
            transaction_result={"score": txn_score, "reasons": []},
            exposure_result={"score": exp_score, "matched": record["card_exposed"], "reasons": []},
            card_result={"score": card_score, "is_expired": record.get("card_expired", False), "reasons": []},
            token_result={"score": tok_score, "is_zombie": record.get("is_zombie_token", False), "reasons": []},
            customer_risk_tier="LOW"
        )
        return res["composite_score"]

    def compute_metrics(
        self,
        y_true: List[int],
        y_scores: List[float],
        threshold: float = 75.0,
        fp_cost: float = DEFAULT_FP_COST,
        fn_cost: float = DEFAULT_FN_COST
    ) -> Dict[str, Any]:
        tp = fp = tn = fn = 0
        for yt, score in zip(y_true, y_scores):
            pred = 1 if score >= threshold else 0
            if yt == 1 and pred == 1:
                tp += 1
            elif yt == 0 and pred == 1:
                fp += 1
            elif yt == 0 and pred == 0:
                tn += 1
            elif yt == 1 and pred == 0:
                fn += 1

        total = len(y_true)
        accuracy = (tp + tn) / total if total > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
        expected_cost = (fp * fp_cost) + (fn * fn_cost)

        return {
            "threshold": threshold,
            "total_samples": total,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "specificity": round(specificity, 4),
            "fpr": round(fpr, 4),
            "fnr": round(fnr, 4),
            "fp_cost_unit": fp_cost,
            "fn_cost_unit": fn_cost,
            "expected_cost": round(expected_cost, 2)
        }

    def evaluate_dataset(
        self,
        split: str = "test.jsonl",
        threshold: float = 75.0,
        fp_cost: float = DEFAULT_FP_COST,
        fn_cost: float = DEFAULT_FN_COST
    ) -> Dict[str, Any]:
        records = self.load_dataset(split)
        y_true = [r["label"] for r in records]
        y_scores = [self.predict_record(r, model_type="full") for r in records]
        return self.compute_metrics(y_true, y_scores, threshold, fp_cost, fn_cost)

    def run_ablation_study(self, split: str = "test.jsonl", threshold: float = 75.0) -> List[Dict[str, Any]]:
        records = self.load_dataset(split)
        y_true = [r["label"] for r in records]

        models = [
            ("Baseline Rule Engine", "baseline_rule"),
            ("Transaction Signals Only", "txn_only"),
            ("Transaction + Card Exposure", "txn_exposure"),
            ("Transaction + Exposure + Token", "txn_exposure_token"),
            ("Full Risk Manager Agent Model", "full"),
        ]

        results = []
        for name, mtype in models:
            scores = [self.predict_record(r, model_type=mtype) for r in records]
            metrics = self.compute_metrics(y_true, scores, threshold)
            metrics["model_name"] = name
            results.append(metrics)
        return results

    def run_threshold_sweep(self, split: str = "test.jsonl") -> List[Dict[str, Any]]:
        records = self.load_dataset(split)
        y_true = [r["label"] for r in records]
        y_scores = [self.predict_record(r, model_type="full") for r in records]

        thresholds = [20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
        results = []
        for th in thresholds:
            m = self.compute_metrics(y_true, y_scores, threshold=th)
            results.append(m)
        return results
