# Data Retention Policy & Secure Lifecycle Management

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  

---

## 1. Configurable Retention Schedules

| Data Entity | Retention Period | Storage Classification | Deletion / Archival Action | Integrity Requirements |
| :--- | :--- | :--- | :--- | :--- |
| **Tamper-Evident Audit Ledger** | 365 Days | RESTRICTED | Immutable block retention | Cryptographic SHA-256 chain verification |
| **Security Cases** | 180 Days | CONFIDENTIAL | Archived to cold storage | Linked to audit events |
| **Transactions & Screenings** | 90 Days | CONFIDENTIAL | Soft-delete / purged by `retention_cleanup.py` | Masked identifiers only |
| **Cloudflare Edge Events** | 30 Days | INTERNAL | Purged by `retention_cleanup.py` | Zero cookies/secrets ingested |
| **DLP Violation Logs** | 60 Days | RESTRICTED | Purged by `retention_cleanup.py` | Contains only masked samples |
| **Ephemeral Demo State** | On-Demand | INTERNAL | Instantly reset via `scripts/reset_demo.py` | Preserves frozen evaluation datasets |

---

## 2. Automated Cleanup Verification

Run the automated cleanup script:
```bash
python scripts/retention_cleanup.py
```
This utility purges telemetry older than the retention threshold while preserving 100% of the cryptographic audit hash chain.
