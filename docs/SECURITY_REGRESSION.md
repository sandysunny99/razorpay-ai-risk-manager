# SECURITY REGRESSION REPORT

## Test Discovery

- **Authentication / RBAC**: test_rbac_auth.py
- **Tenant isolation**: test_multi_tenancy.py
- **Webhook security**: test_enrichment_and_webhooks.py, test_webhook_live.py
- **Cryptography / encryption**: NO_DEDICATED_TEST_FILE
- **DLP**: NO_DEDICATED_TEST_FILE
- **Audit ledger**: test_audit_chain.py
- **Policy Engine**: test_policy.py
- **Zombie Card Saver**: test_zombie_card_saver.py
- **Prompt injection**: test_adversarial_threat.py
- **Razorpay**: test_razorpay_integration.py
- **Cloudflare**: NO_DEDICATED_TEST_FILE

## Authentication / RBAC
Status: COVERAGE_GAP
```
no tests ran in 0.00s

STDERR:
ERROR: file or directory not found: test_rbac_auth.py
```

## Tenant isolation
Status: COVERAGE_GAP
```
no tests ran in 0.00s

STDERR:
ERROR: file or directory not found: test_multi_tenancy.py
```

## Webhook security
Status: COVERAGE_GAP
```
no tests ran in 0.00s

STDERR:
ERROR: file or directory not found: test_enrichment_and_webhooks.py
```

## Audit ledger
Status: COVERAGE_GAP
```
no tests ran in 0.00s

STDERR:
ERROR: file or directory not found: test_audit_chain.py
```

## Policy Engine
Status: COVERAGE_GAP
```
no tests ran in 0.00s

STDERR:
ERROR: file or directory not found: test_policy.py
```

## Zombie Card Saver
Status: COVERAGE_GAP
```
no tests ran in 0.00s

STDERR:
ERROR: file or directory not found: test_zombie_card_saver.py
```

## Prompt injection
Status: COVERAGE_GAP
```
no tests ran in 0.00s

STDERR:
ERROR: file or directory not found: test_adversarial_threat.py
```

## Razorpay
Status: COVERAGE_GAP
```
no tests ran in 0.00s

STDERR:
ERROR: file or directory not found: test_razorpay_integration.py
```

## Bandit
Status: PASS
```

```

## Ruff
Status: FAIL
```
I001 [*] Import block is un-sorted or un-formatted
  --> backend\app\api\routes_webhooks.py:1:1
   |
 1 | / import hashlib
 2 | | import json
 3 | | import logging
 4 | | from datetime import datetime
 5 | | from typing import Optional
 6 | |
 7 | | from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
 8 | | from sqlalchemy.orm import Session
 9 | |
10 | | from app.core.database import get_db
11 | | from app.events.event_bus import event_bus
12 | | from app.events.event_normalizer import EventNormalizer
13 | | from app.integrations.razorpay_adapter import RazorpayTestAdapter
14 | | from app.models.entities import WebhookEvent
15 | | from app.security.dlp import DLPEngine
   | |______________________________________^
16 |
17 |   router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
   |
help: Organize imports
  |
1 + from datetime import datetime
2 | import hashlib
3 | import json
4 | import logging
  - from datetime import datetime
5 | from typing import Optional
  |

F401 [*] `secrets` imported but unused
 --> backend\app\core\config.py:1:8
  |
1 | import secrets
  |        ^^^^^^^
2 | from typing import List
  |
help: Remove unused import: `secrets`
  |
  - import secrets
1 | from typing import List
  |

E401 [*] Multiple imports on one line
  --> backend\app\core\config.py:43:9
   |
41 |         if self._ephemeral_secret is not None:
42 |             return self._ephemeral_secret
43 |         import warnings, secrets
   |         ^^^^^^^^^^^^^^^^^^^^^^^^
44 |
45 |         warnings.warn(
   |
help: Split imports
   |
42 |             return self._ephemeral_secret
   -         import warnings, secrets
43 +         import warnings
44 +         import secrets
45 |
   |

I001 [*] Import block is un-sorted or un-formatted
  --> backend\app\core\config.py:43:9
   |
41 |         if self._ephemeral_secret is not None:
42 |             return self._ephemeral_secret
43 |         import warnings, secrets
   |         ^^^^^^^^^^^^^^^^^^^^^
```

## Frozen Test Set Integrity
Status: PASS
```
Checking test set integrity...
Target: c:\Users\sunny\Downloads\RAZAORPAY AI\evaluation\test.jsonl
Expected SHA-256: 76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f
Computed SHA-256: 76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f
[PASS] TEST_SET_INTEGRITY = PASS (Frozen test set is verified & untouched)
```

## Release Guard
Status: PASS
```
======================================================================
RAZORPAY AI RISK MANAGER: RELEASE GUARD
======================================================================
[PASS] Held-Out Test Set SHA-256 Verified: 76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f
[PASS] File found: evaluation/train.jsonl
[PASS] File found: evaluation/validation.jsonl
[PASS] File found: evaluation/test.jsonl
[PASS] File found: backend/app/main.py
[PASS] File found: backend/app/agent/risk_agent.py
[PASS] File found: backend/app/engines/policy_engine.py
[PASS] File found: backend/app/engines/risk_scorer.py
[PASS] File found: backend/app/integrations/razorpay_adapter.py
[PASS] File found: frontend/src/App.tsx
[PASS] File found: frontend/src/components/EvaluationDashboard.tsx
[PASS] File found: frontend/src/components/InvestigationTimeline.tsx
[PASS] File found: README.md
[PASS] File found: docs/FINAL_EVALUATION.md
[PASS] File found: docs/FINAL_READINESS.md
[PASS] Dataset Isolation & Schema Checked: 2000 unique transaction records across 3 splits (Zero Leakage)
[PASS] Policy Engine Configuration & Response Boundaries Verified.
----------------------------------------------------------------------
[SUCCESS] ALL RELEASE GUARD CHECKS PASSED. SYSTEM IS READY.
======================================================================
```

## Full Test Suite
Status: PASS
```
..............................................s......................... [ 75%]
.......................                                                  [100%]
============================== warnings summary ===============================
backend\app\core\security.py:58
  c:\Users\sunny\Downloads\RAZAORPAY AI\backend\app\core\security.py:58: RuntimeWarning: HMAC_SECRET_KEY not set — using ephemeral random key. Set HMAC_SECRET_KEY env var for stable production operation.
    key = (salt or settings.hmac_secret_resolved).encode("utf-8")

..\..\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\sunny\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

backend/tests/test_agent_benchmark.py: 602 warnings
backend/tests/test_database.py: 7 warnings
backend/tests/test_e2e_agent.py: 24 warnings
backend/tests/test_enrichment_and_webhooks.py: 1 warning
backend/tests/test_multi_tenancy.py: 114 warnings
backend/tests/test_rbac_auth.py: 20 warnings
backend/tests/test_tiered_response.py: 12 warnings
backend/tests/test_two_layer_metrics.py: 25 warnings
backend/tests/test_webapp_security.py: 1 warning
  C:\Users\sunny\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\sql\schema.py:3624: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore

backend/tests/test_enrichment_and_webhooks.py::test_webhook_api_endpoint_ingestion_and_dlp
backend/tests/test_enrichment_and_webhooks.py::test_webhook_api_endpoint_ingestion_and_dlp
  c:\Users\sunny\Downloads\RAZAORPAY AI\backend\app\api\routes_webhooks.py:77: De
```

---
## Summary
SECURITY REGRESSIONS: 0
QUALITY GATE FAILURES: 1
COVERAGE GAPS: 3
ENVIRONMENT FAILURES: 0
OVERALL: PASS