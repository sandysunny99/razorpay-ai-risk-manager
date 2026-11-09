"""Runtime LightGBM scoring with per-decision reasons.

Reasons come from LightGBM's built-in TreeSHAP (``pred_contrib=True``), so no separate SHAP
dependency is needed. The scorer is fail-safe: if lightgbm or the model file is missing, or
scoring raises, it returns None and the deterministic pipeline continues unchanged.
"""
import json
import logging
import math
import os
from pathlib import Path
import threading
from typing import List, Optional

from backend.ml.features import FEATURES, READABLE

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent / "model"
MODEL_PATH = Path(os.getenv("NETVRIO_ML_MODEL", str(MODEL_DIR / "netvrio_lgbm.txt")))


def escalation_enabled() -> bool:
    return os.getenv("NETVRIO_ML_ESCALATE", "false").lower() == "true"


def escalation_threshold() -> float:
    try:
        return min(0.99, max(0.5, float(os.getenv("NETVRIO_ML_THRESHOLD", "0.8"))))
    except ValueError:
        return 0.8


class MlScorer:
    def __init__(self, model_path: Path = MODEL_PATH):
        self._path = model_path
        self._booster = None
        self._loaded = False
        self._lock = threading.Lock()
        self.error: Optional[str] = None

    def _load(self):
        with self._lock:
            if self._loaded:
                return self._booster
            self._loaded = True
            try:
                import lightgbm as lgb

                self._booster = lgb.Booster(model_file=str(self._path))
                if list(self._booster.feature_name()) != FEATURES:
                    raise ValueError("model features do not match the feature contract")
            except Exception as exc:  # noqa: BLE001
                self._booster = None
                self.error = f"{type(exc).__name__}"
                logger.warning("ML scorer unavailable: %s", self.error)
            return self._booster

    @property
    def available(self) -> bool:
        return self._load() is not None

    def score(self, features: List[float], top_k: int = 3) -> Optional[dict]:
        booster = self._load()
        if booster is None:
            return None
        try:
            import numpy as np

            x = np.array([features], dtype=float)
            probability = float(booster.predict(x)[0])
            contrib = booster.predict(x, pred_contrib=True)[0]  # per-feature log-odds + bias (last)
            pairs = sorted(zip(FEATURES, contrib[:-1], features), key=lambda t: abs(t[1]), reverse=True)
            reasons = [
                {
                    "feature": READABLE.get(name, name),
                    "direction": "raises" if c > 0 else "lowers",
                    "contribution": round(float(c), 3),
                    "value": None if (isinstance(v, float) and math.isnan(v)) else round(float(v), 3),
                }
                for name, c, v in pairs[:top_k]
                if abs(c) > 1e-6
            ]
            return {"model": "lightgbm", "probability": round(probability, 4), "reasons": reasons}
        except Exception as exc:  # noqa: BLE001 — scoring must never break the payment path
            logger.warning("ML scoring failed: %s", type(exc).__name__)
            return None

    def card(self) -> dict:
        try:
            card = json.loads((MODEL_DIR / "model_card.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            card = {}
        return {
            "available": self.available,
            "error": self.error,
            "escalation_enabled": escalation_enabled(),
            "escalation_threshold": escalation_threshold(),
            **card,
        }


ml_scorer = MlScorer()
