from typing import Any, Dict, List

from fastapi import APIRouter, Query

from app.evaluation.evaluator import ModelEvaluator

router = APIRouter(prefix="/evaluation", tags=["Model Evaluation & Metrics"])
evaluator = ModelEvaluator()

@router.get("/metrics")
def get_evaluation_metrics(
    split: str = Query("test.jsonl", description="Dataset split (test.jsonl, validation.jsonl, train.jsonl)"),
    threshold: float = Query(75.0, description="Risk decision threshold (0-100)"),
    fp_cost: float = Query(100.0, description="Cost of false positive in INR"),
    fn_cost: float = Query(5000.0, description="Cost of false negative in INR")
) -> Dict[str, Any]:
    """Calculates precision, recall, F1, confusion matrix, and expected business cost."""
    return evaluator.evaluate_dataset(split=split, threshold=threshold, fp_cost=fp_cost, fn_cost=fn_cost)

@router.get("/ablation")
def get_ablation_study(
    split: str = Query("test.jsonl", description="Dataset split (test.jsonl, validation.jsonl, train.jsonl)"),
    threshold: float = Query(75.0, description="Risk decision threshold")
) -> List[Dict[str, Any]]:
    """Runs ablation comparison across baseline heuristic, sub-models, and full model."""
    return evaluator.run_ablation_study(split=split, threshold=threshold)

@router.get("/thresholds")
def get_threshold_sweep(
    split: str = Query("test.jsonl", description="Dataset split (test.jsonl, validation.jsonl, train.jsonl)")
) -> List[Dict[str, Any]]:
    """Runs threshold sensitivity sweep across thresholds 20 to 90."""
    return evaluator.run_threshold_sweep(split=split)

@router.get("/transactions")
def list_evaluation_transactions(
    split: str = Query("test.jsonl", description="Dataset split"),
    limit: int = Query(50, description="Number of transactions to return"),
    offset: int = Query(0, description="Offset for pagination")
) -> Dict[str, Any]:
    """Returns scored transactions from the evaluation set for live risk monitoring."""
    records = evaluator.load_dataset(split=split)
    total = len(records)
    sliced = records[offset:offset+limit]

    scored_items = []
    for r in sliced:
        score = evaluator.predict_record(r, model_type="full")
        severity = "CRITICAL" if score >= 75.0 else ("HIGH" if score >= 60.0 else ("MEDIUM" if score >= 25.0 else "LOW"))
        scored_items.append({
            **r,
            "calculated_risk_score": score,
            "severity": severity,
            "recommended_action": "REVOKE_TOKEN" if score >= 75.0 else ("MONITOR" if score >= 25.0 else "ALLOW")
        })

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "transactions": scored_items
    }

@router.get("/errors")
def get_error_analysis(
    split: str = Query("test.jsonl", description="Dataset split"),
    threshold: float = Query(75.0, description="Risk decision threshold")
) -> Dict[str, Any]:
    """Runs detailed False Negative & False Positive error diagnostics."""
    from app.evaluation.error_analysis import run_error_analysis
    return run_error_analysis(split=split, threshold=threshold)

@router.get("/tiers")
def get_policy_tier_distribution(
    split: str = Query("validation.jsonl", description="Dataset split (validation.jsonl, test.jsonl, train.jsonl)")
) -> Dict[str, Any]:
    """Computes distribution across Response Tiers: LOW, MONITOR, STEP_UP, REVIEW, AUTO_REMEDIATE."""
    from app.engines.policy_engine import PolicyEngine
    policy = PolicyEngine()
    records = evaluator.load_dataset(split=split)

    tier_counts = {"LOW": 0, "MONITOR": 0, "STEP_UP": 0, "REVIEW": 0, "AUTO_REMEDIATE": 0}
    action_counts = {}

    for r in records:
        score = evaluator.predict_record(r, model_type="full")
        tier_info = policy.classify_risk_tier(score, context=r)
        tier = tier_info["response_tier"]
        act = tier_info["recommended_action"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        action_counts[act] = action_counts.get(act, 0) + 1

    return {
        "split": split,
        "total_records": len(records),
        "tier_counts": tier_counts,
        "action_counts": action_counts
    }


