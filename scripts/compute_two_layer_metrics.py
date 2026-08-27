import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, 'backend')
from app.evaluation.evaluator import ModelEvaluator

evaluator = ModelEvaluator()
test_path = Path('evaluation/test.jsonl')
with open(test_path, 'rb') as f:
    h = hashlib.sha256(f.read()).hexdigest()

metrics_40 = evaluator.evaluate_dataset('test.jsonl', threshold=40.0)
metrics_75 = evaluator.evaluate_dataset('test.jsonl', threshold=75.0)

print(f"TEST_SET_HASH: {h}")
print(f"TEST_SIZE: {metrics_40['total_samples']}")
print("--- T=40 (Broad Detection) ---")
print(json.dumps(metrics_40, indent=2))
print("--- T=75 (Autonomous Remediation) ---")
print(json.dumps(metrics_75, indent=2))
