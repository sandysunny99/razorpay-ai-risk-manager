"""Transaction simulator with injected fraud scenarios (after the Fraud Detection Handbook approach).

The bundled evaluation/*.jsonl set is not suitable for training: a single feature (velocity)
separates its labels perfectly, so a model trained on it ignores the zombie and exposure signals.
This simulator produces overlapping, noisy distributions so the model must combine signals:

  legit         busy customers, travellers, cards exposed but not yet abused, new devices
  card_testing  bursts of small payments, failed attempts, new devices
  zombie_abuse  expired or replaced card tokens reused at ordinary velocity
  exposed_use   leaked cards used from new devices, often abroad
  takeover      new device and country with a large payment

Labels carry 2% noise. Everything is synthetic and seeded for reproducibility.
"""
import math
import random
from typing import List, Tuple

from backend.ml.features import FEATURES

FRAUD_MIX = {"card_testing": 0.30, "zombie_abuse": 0.30, "exposed_use": 0.25, "takeover": 0.15}


def _row(rng: random.Random, kind: str) -> dict:
    r = {
        "log_amount": math.log1p(rng.lognormvariate(6.4, 1.2)),
        "velocity": 1 + min(int(rng.expovariate(1.0)), 4),
        "country_mismatch": 1.0 if rng.random() < 0.03 else 0.0,
        "card_exposed": 0.0,
        "exposure_confidence": 0.0,
        "token_active": 1.0 if rng.random() > 0.005 else 0.0,
        "token_age_days": rng.uniform(0, 900),
        "is_zombie_token": 0.0,
        "card_expired": 0.0,
        "device_new": 1.0 if rng.random() < 0.12 else 0.0,
        "failed_attempts": float(min(int(rng.expovariate(4.0)), 3)),
    }
    if kind == "legit":
        roll = rng.random()
        if roll < 0.06:  # busy but genuine customer
            r["velocity"] = rng.randint(4, 10)
        elif roll < 0.09:  # card exposed somewhere, not (yet) abused
            r["card_exposed"], r["exposure_confidence"] = 1.0, rng.uniform(0.2, 0.9)
        elif roll < 0.11:  # traveller on a new device
            r["country_mismatch"], r["device_new"] = 1.0, 1.0
        elif roll < 0.115:  # legitimate retry on a renewed card
            r["card_expired"] = 1.0
    elif kind == "card_testing":
        r["log_amount"] = math.log1p(rng.uniform(1, 150))
        r["velocity"] = rng.randint(4, 15)
        r["failed_attempts"] = float(rng.randint(1, 8))
        r["device_new"] = 1.0 if rng.random() < 0.7 else 0.0
    elif kind == "zombie_abuse":
        r["is_zombie_token"] = 1.0
        r["card_expired"] = 1.0 if rng.random() < 0.6 else 0.0
        r["velocity"] = rng.randint(1, 3)
        r["token_age_days"] = rng.uniform(300, 1500)
        r["log_amount"] = math.log1p(rng.uniform(100, 5000))
    elif kind == "exposed_use":
        r["card_exposed"], r["exposure_confidence"] = 1.0, rng.uniform(0.55, 1.0)
        r["device_new"] = 1.0 if rng.random() < 0.8 else 0.0
        r["country_mismatch"] = 1.0 if rng.random() < 0.5 else 0.0
        r["log_amount"] = math.log1p(rng.lognormvariate(8.5, 1.0))
        r["velocity"] = rng.randint(1, 4)
    elif kind == "takeover":
        r["device_new"] = 1.0
        r["country_mismatch"] = 1.0 if rng.random() < 0.7 else 0.0
        r["log_amount"] = math.log1p(rng.lognormvariate(9.5, 0.8))
        r["failed_attempts"] = float(rng.randint(0, 3))
    return r


def simulate(n: int, fraud_rate: float = 0.08, noise: float = 0.02, seed: int = 7) -> Tuple[List[List[float]], List[int]]:
    rng = random.Random(seed)
    kinds, weights = zip(*FRAUD_MIX.items())
    xs, ys = [], []
    for _ in range(n):
        fraud = rng.random() < fraud_rate
        kind = rng.choices(kinds, weights=weights)[0] if fraud else "legit"
        row = _row(rng, kind)
        label = int(fraud)
        if rng.random() < noise:
            label = 1 - label
        xs.append([float(row[f]) for f in FEATURES])
        ys.append(label)
    return xs, ys
