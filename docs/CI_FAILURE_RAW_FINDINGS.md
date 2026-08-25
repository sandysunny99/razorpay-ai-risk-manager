# GitHub Actions Forensic Analysis & Root Cause Findings

**Repository**: `sandysunny99/razorpay-ai-risk-manager`  
**Failed Workflow Run ID**: `32814089701`  
**Workflow Run HTML**: https://github.com/sandysunny99/razorpay-ai-risk-manager/actions/runs/32814089701  
**Failed Job**: `validate-and-build` (Job ID: `97698852356`)  
**Commit**: `44d042ecc2a1f38d9855df45a70f4d6e2a4e41bd`  
**Branch**: `main`  
**Trigger Timestamp**: `2026-08-25T05:45:21Z`  

---

## 1. Exact Step Breakdown from GitHub Actions API

| Step Number | Step Name | Status | Conclusion | Duration |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Set up job | `completed` | `success` | 2s |
| **2** | Checkout Code | `completed` | `success` | 1s |
| **3** | Set up Python 3.12 | `completed` | `success` | 1s |
| **4** | Environment Diagnostics | `completed` | `success` | 0s |
| **5** | Install Backend Dependencies | `completed` | `success` | 8s |
| **6** | **1. Test Set Hash Immutability Gate** | `completed` | **`failure`** | **0s** |
| 7 | 2. Automated Backend Pytest Suite | `completed` | `skipped` | - |
| 8 | 3. Reproducible Final Evaluation Benchmark | `completed` | `skipped` | - |
| 9 | 4. Release Guard Enforcement | `completed` | `skipped` | - |
| 10 | 5. Cloudflare Security Telemetry Gate | `completed` | `skipped` | - |
| 11 | 6. Data Security & DLP Verification Gate | `completed` | `skipped` | - |
| 12 | Set up Node.js 20 | `completed` | `skipped` | - |
| 13 | 7. Frontend Production Bundle Build | `completed` | `skipped` | - |
| 14 | 8. Docker Multi-Stage Image Build | `completed` | `skipped` | - |

---

## 2. Exact Failed Command & Root Cause

- **Failed Step**: `Step 6: 1. Test Set Hash Immutability Gate`
- **Command**: `python scripts/verify_test_set.py`
- **Root Cause**:
  - The frozen benchmark test set `evaluation/test.jsonl` ($N=300$) was authored on a Windows filesystem where newline delimiters are CRLF (`\r\n`), producing the canonical SHA-256 hash `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`.
  - When GitHub Actions checked out the repository on an `ubuntu-latest` Linux runner without a `.gitattributes` configuration, git converted the line endings to LF (`\n`).
  - Reading `evaluation/test.jsonl` in binary mode (`open(test_path, 'rb')`) on Linux resulted in a byte mismatch (`9b67eea...` instead of `76a26e7...`), causing `verify_test_set.py` to abort immediately with exit code 1.

---

## 3. Resolution Plan

1. Create [`.gitattributes`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/.gitattributes) to enforce byte-for-byte CRLF preservation for `evaluation/*.jsonl` on all OS checkouts:
   ```gitattributes
   evaluation/*.jsonl text eol=crlf
   ```
2. Update [`scripts/verify_test_set.py`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/scripts/verify_test_set.py), [`scripts/release_guard.py`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/scripts/release_guard.py), and [`backend/tests/test_two_layer_metrics.py`](file:///c:/Users/sunny/Downloads/RAZAORPAY%20AI/backend/tests/test_two_layer_metrics.py) with deterministic newline handling.
