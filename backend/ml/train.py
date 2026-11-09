"""Train the LightGBM second-opinion model.

    python -m backend.ml.train

Training data comes from the scenario simulator (backend/ml/simulate.py), because the bundled
evaluation set is separable by velocity alone (see the label and shortcut audits in the model
card). The frozen evaluation/test.jsonl is never used for fitting; it is reported only as a
cross-dataset check. Writes the model and a model card with measured metrics to backend/ml/model/.
scikit-learn is needed for metrics at training time only; the API needs just lightgbm and numpy.
"""
import json
import math
from pathlib import Path
import random

import lightgbm as lgb
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve

from backend.ml.features import FEATURES, NAN, OFTEN_MISSING, from_training_row
from backend.ml.simulate import simulate

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "model"
SEED = 2026
MASK_RATE = 0.3

# Risk signals may only push the score up (token_active only down). Stops the model from learning
# "a zombie token at normal velocity is safe" from any artefact in the data.
MONOTONE = {
    "velocity": 1, "country_mismatch": 1, "card_exposed": 1, "exposure_confidence": 1, "token_active": -1,
    "is_zombie_token": 1, "card_expired": 1, "device_new": 1, "failed_attempts": 1,
}

# Live-style inputs the model must rank sensibly; recorded in the model card.
PROBES = {
    "ordinary payment": {"log_amount": math.log1p(500), "velocity": 1},
    "zombie token, normal velocity": {"log_amount": math.log1p(800), "velocity": 1, "is_zombie_token": 1, "card_expired": 1},
    "exposed card (0.9), new device": {"log_amount": math.log1p(9000), "velocity": 1, "card_exposed": 1, "exposure_confidence": 0.9, "device_new": 1},
    "card testing burst": {"log_amount": math.log1p(20), "velocity": 9, "failed_attempts": 4, "device_new": 1},
    "busy genuine customer": {"log_amount": math.log1p(600), "velocity": 6},
}


def load_eval(name: str):
    rows = [json.loads(line) for line in (ROOT / "evaluation" / name).read_text(encoding="utf-8").splitlines() if line.strip()]
    return np.array([from_training_row(r) for r in rows], dtype=float), np.array([int(r["label"]) for r in rows])


def mask_missing(x: np.ndarray, rng: random.Random) -> np.ndarray:
    x = x.copy()
    idx = [FEATURES.index(f) for f in OFTEN_MISSING]
    for row in x:
        for j in idx:
            if rng.random() < MASK_RATE:
                row[j] = NAN
    return x


def probe_vector(spec: dict) -> list:
    base = {f: 0.0 for f in FEATURES}
    base.update({"token_active": 1.0, "token_age_days": NAN, "country_mismatch": NAN, "failed_attempts": NAN})
    base.update(spec)
    return [float(base[f]) for f in FEATURES]


def audits() -> dict:
    """Why the bundled evaluation set is not used for training."""
    rows = [json.loads(line) for line in (ROOT / "evaluation" / "train.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rule = lambda r: (r["card_exposed"] and r["exposure_confidence"] >= 0.7) or r["is_zombie_token"]  # noqa: E731
    fraud_v = [r["velocity_10m"] for r in rows if r["label"] == 1]
    legit_v = [r["velocity_10m"] for r in rows if r["label"] == 0]
    return {
        "label_rule": "(card_exposed and exposure_confidence >= 0.7) or is_zombie_token",
        "label_rule_agreement": round(float(np.mean([int(bool(rule(r))) == int(r["label"]) for r in rows])), 4),
        "velocity_shortcut": {"fraud_min_velocity": min(fraud_v), "legit_max_velocity": max(legit_v)},
    }


def recall_at_fpr(y, p, fpr_target):
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max(tpr[fpr <= fpr_target])) if np.any(fpr <= fpr_target) else 0.0


def report(booster, x, y) -> dict:
    p = booster.predict(x)
    return {
        "pr_auc": round(float(average_precision_score(y, p)), 4),
        "roc_auc": round(float(roc_auc_score(y, p)), 4),
        "recall_at_1pct_fpr": round(recall_at_fpr(y, p, 0.01), 4),
        "recall_at_5pct_fpr": round(recall_at_fpr(y, p, 0.05), 4),
        "fraud_rate": round(float(np.mean(y)), 4),
        "n": int(len(y)),
    }


def main() -> None:
    rng = random.Random(SEED)
    x_all, y_all = simulate(30_000, seed=SEED)
    x_all, y_all = np.array(x_all), np.array(y_all)
    x_tr, y_tr = x_all[:20_000], y_all[:20_000]
    x_va, y_va = x_all[20_000:25_000], y_all[20_000:25_000]
    x_te, y_te = x_all[25_000:], y_all[25_000:]
    x_tr = mask_missing(x_tr, rng)

    pos = y_tr.sum()
    params = {
        "objective": "binary",
        "learning_rate": 0.05,
        "num_leaves": 15,
        "min_data_in_leaf": 40,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.9,
        "bagging_freq": 1,
        "scale_pos_weight": float((len(y_tr) - pos) / pos),  # class imbalance
        "monotone_constraints": [MONOTONE.get(f, 0) for f in FEATURES],
        "seed": SEED,
        "deterministic": True,
        "verbose": -1,
    }
    booster = lgb.train(
        params,
        lgb.Dataset(x_tr, y_tr, feature_name=FEATURES),
        num_boost_round=800,
        valid_sets=[lgb.Dataset(x_va, y_va, feature_name=FEATURES)],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )
    booster = lgb.Booster(model_str=booster.model_to_string(num_iteration=booster.best_iteration))

    x_te_missing = x_te.copy()
    for f in OFTEN_MISSING:
        x_te_missing[:, FEATURES.index(f)] = NAN
    x_ev, y_ev = load_eval("test.jsonl")

    OUT.mkdir(exist_ok=True)
    booster.save_model(str(OUT / "netvrio_lgbm.txt"))
    card = {
        "model": "LightGBM binary classifier. Second opinion only: it can escalate an ALLOW to REVIEW, never block.",
        "lightgbm_version": lgb.__version__,
        "features": FEATURES,
        "monotone_constraints": MONOTONE,
        "training_data": "backend/ml/simulate.py: 30k synthetic rows, 8% fraud in 4 scenarios, 2% label noise; 20k/5k/5k split",
        "missingness_augmentation": {"features": OFTEN_MISSING, "rate": MASK_RATE, "seed": SEED},
        "holdout_metrics": report(booster, x_te, y_te),
        "holdout_metrics_live_fields_missing": report(booster, x_te_missing, y_te),
        "cross_dataset_metrics_evaluation_test": report(booster, x_ev, y_ev),
        "probes": {k: round(float(booster.predict(np.array([probe_vector(v)]))[0]), 4) for k, v in PROBES.items()},
        "why_not_evaluation_set": audits(),
        "caveat": (
            "Trained and measured on synthetic data, so the numbers describe the simulator, not real Razorpay "
            "traffic. Retrain on labelled production data before relying on it; keep NETVRIO_ML_ESCALATE off until then "
            "unless you are demonstrating the flow."
        ),
    }
    (OUT / "model_card.json").write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: card[k] for k in ("holdout_metrics", "cross_dataset_metrics_evaluation_test", "probes")}, indent=2))


if __name__ == "__main__":
    main()
