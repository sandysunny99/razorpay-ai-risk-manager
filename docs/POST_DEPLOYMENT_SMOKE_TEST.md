# Post-Deployment Verification & Smoke Test Runbook

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  

---

## 1. Step-by-Step Production Smoke Test Checklist

Execute the following sequential test steps against the running service:

### Step 1: Health & Dependency Liveness
```bash
curl -s http://localhost:8000/health
# Expected: {"status":"healthy","service":"Razorpay AI Risk Manager Gateway","version":"2.0.0-rc1"}

curl -s http://localhost:8000/api/v1/health/dependencies
# Expected: {"status":"healthy","dependencies":{"sqlite_database":"UP","cloudflare_edge_adapter":"UP", ...}}
```

### Step 2: Data Protection & Key Management Status
```bash
curl -s http://localhost:8000/api/v1/security/data-protection
# Expected: {"status":"PASS","data_at_rest":{"status":"PASS","storage_encryption":"AES-256-GCM Authenticated Field Encryption", ...}}
```

### Step 3: Interactive DLP Scrubber Test
```bash
curl -s -X POST http://localhost:8000/api/v1/security/dlp/test \
  -H "Content-Type: application/json" \
  -d '{"input_text": "Payment with card 4111 1111 1111 1111 and key rzp_live_9a8b7c6d5e"}'
# Expected: {"violations_detected": 2, "sanitized_output": "Payment with card **** **** **** 1111 and key [REDACTED_API_KEY]"}
```

### Step 4: Golden Demo Scenario Execution
- Open frontend dashboard at `http://localhost:5173`.
- Click **Trigger Golden Demo Scenario (Stealer Dump + Zombie Token)**.
- Confirm agent investigates with Level 3 depth, enforces Policy `PR-01`, autonomously revokes vault token, verifies state transition, recalculates risk ($94 \rightarrow 16$), and links to cryptographic audit ledger.

### Step 5: Audit Ledger Cryptographic Verification
- Navigate to **Tamper-Evident Audit Trail** tab.
- Click **Verify Cryptographic Chain**.
- Confirm status: `CRYPTOGRAPHIC_INTEGRITY_VERIFIED (0 Tampered Blocks)`.
