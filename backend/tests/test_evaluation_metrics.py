
import pytest

from app.evaluation.evaluator import ModelEvaluator


@pytest.fixture
def evaluator():
    return ModelEvaluator()

def test_held_out_dataset_loading(evaluator):
    records = evaluator.load_dataset("test.jsonl")
    assert len(records) == 300
    assert all("transaction_id" in r for r in records)
    assert all("label" in r for r in records)

def test_confusion_matrix_sum_and_integrity(evaluator):
    metrics = evaluator.evaluate_dataset("test.jsonl", threshold=75.0)
    assert metrics["total_samples"] == 300
    assert metrics["tp"] + metrics["fp"] + metrics["tn"] + metrics["fn"] == 300
    assert metrics["precision"] >= 0.90
    assert metrics["fpr"] == 0.0  # Zero False Positives on held-out test data

def test_expected_cost_formula(evaluator):
    # Test cost calculation
    y_true = [1, 1, 0, 0]
    y_scores = [80.0, 40.0, 90.0, 10.0] # TP=1, FN=1, FP=1, TN=1
    m = evaluator.compute_metrics(y_true, y_scores, threshold=75.0, fp_cost=100.0, fn_cost=5000.0)
    assert m["tp"] == 1
    assert m["fn"] == 1
    assert m["fp"] == 1
    assert m["tn"] == 1
    assert m["expected_cost"] == (1 * 100.0) + (1 * 5000.0)

def test_ablation_study_execution(evaluator):
    ablation = evaluator.run_ablation_study("test.jsonl", threshold=75.0)
    assert len(ablation) == 5
    model_names = [a["model_name"] for a in ablation]
    assert "Baseline Rule Engine" in model_names
    assert "Full Risk Manager Agent Model" in model_names

def test_threshold_sweep_bounds(evaluator):
    sweep = evaluator.run_threshold_sweep("test.jsonl")
    assert len(sweep) == 9
    for entry in sweep:
        assert 0.0 <= entry["precision"] <= 1.0
        assert 0.0 <= entry["recall"] <= 1.0
        assert 0.0 <= entry["accuracy"] <= 1.0
