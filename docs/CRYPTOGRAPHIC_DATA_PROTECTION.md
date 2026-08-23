# Cryptographic Data Protection & Key Management

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Date**: August 23, 2026  

---

## 1. Cryptographic Primitives & Standards

- **Field-Level Encryption**: AES-256-GCM (Authenticated Encryption with Associated Data).
- **Nonce Generation**: 96-bit cryptographically secure random nonces (`os.urandom(12)`) per encryption operation to guarantee nonce uniqueness.
- **Card Fingerprinting**: HMAC-SHA256 with server-side managed secret salt.
- **Audit Ledger Integrity**: SHA-256 hash-chained block structure (`curr_hash = SHA256(event_data + prev_hash)`).
- **Transport Security**: TLS 1.3 enforced at Cloudflare edge perimeter with HSTS.

---

## 2. Key Lifecycle & Rotation Management

The `EnvironmentKeyProvider` supports key versioning (`v1`, `v2`, `...`) and state tracking:
- `ACTIVE`: Key currently used for both encryption and decryption.
- `RETIRED`: Historical key retained for decrypting legacy ciphertexts; new encryptions use active key.
- `REVOKED`: Key disabled due to compromise; decryption immediately blocked with security alert.
- **Safe Metadata Exposure**: API and SOC dashboards expose only version, algorithm, status, and creation timestamp—**raw key bytes are never leaked**.
