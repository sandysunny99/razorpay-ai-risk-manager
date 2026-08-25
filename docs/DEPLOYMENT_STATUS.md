# Deployment Status & Pre-Flight Checklist

**Repository**: `sandysunny99/razorpay-ai-risk-manager`  
**Current Commit**: `9f00125`  
**Current Release Tag**: `v2.0.0-rc2`  
**Deployment State**: `DEPLOYMENT_CONFIGURED` / `LOCAL_VALIDATED`  

---

## 1. Quality Gates & Release Checklist

- [x] **Held-Out Test Set Immutability**: SHA-256 `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f` verified.
- [x] **63 Automated Backend Tests**: All 63 pytest tests pass (0 failures).
- [x] **Two-Layer Evaluation**: Broad Detection Recall $88.06\%$, Auto-Action Precision $100.00\%$ (0 False Positives).
- [x] **Zombie Card Saver Subsystem**: Detection, severity classifier, merchant impact analysis, and selective remediation validated.
- [x] **Webhook Security**: Raw HMAC-SHA256 signature verification, TTL idempotency, and DLP scrubbing validated.
- [x] **Edge Security Perimeter**: Cloudflare CF-Ray correlation, bot management, and WAF telemetry simulated & verified.
- [x] **Data Security**: AES-256-GCM authenticated encryption, dynamic masking, and key rotation verified.
- [x] **Frontend Production Bundle**: 1,817 modules compiled with 0 TypeScript errors.
- [x] **Docker Multi-Stage Build**: Node 20 alpine frontend builder + Python 3.12 slim backend runner configured with `--legacy-peer-deps`.
- [x] **Secret Audit**: Zero `.env`, credentials, or private keys in git repository.

---

## 2. Deployment Architecture Sequencing

1. **Origin Service (Render)**:
   - Deploy Dockerfile runner.
   - Configure health check `/health`.
   - Set environment variables (`APP_ENV=production`, `DRY_RUN=false`).
2. **Custom Domain & DNS (Cloudflare)**:
   - Point DNS CNAME to Render origin.
   - Provision Universal SSL / TLS 1.3 certificate.
3. **Cloudflare Security Telemetry**:
   - Enable Cloudflare WAF, Bot Management, and HTTP request inspection.
   - Verify CF-Ray ID forwarding into Risk Engine audit logs.
