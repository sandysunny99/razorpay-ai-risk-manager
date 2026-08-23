# Release Candidate Commit Verification (v2.0.0-rc1)

**Project**: Razorpay AI Risk Manager Agent  
**Hackathon**: Razorpay AI Buildathon 2026 (Track: AI Risk Manager)  
**Release Tag**: `v2.0.0-rc1`  
**Branch**: `feature/risk-manager-webapp-security`  
**Commit Hash**: `4a80238c48abdda988a821085058a1dcd069733a`  
**Short Commit**: `4a80238`  
**Commit Message**: `feat(release): freeze v2.0.0-rc1 - accurate HMAC-SHA256 terminology, Render deployment blueprint, and final security evidence matrix`  
**Timestamp**: 2026-08-23T14:52:30+05:30  
**Working Tree State**: `CLEAN (nothing to commit, working tree clean)`  

---

## 1. Verified Immutable Checksums

- **Evaluation Dataset (Held-Out Test Set)**: `evaluation/test.jsonl`
- **Frozen Test Set SHA-256 Checksum**: `76a26e7cef5038a228ba178dc7e1d8e170c4133dc528f28d1764e46609ba8a5f`
- **Total Test Records**: $N = 300$ (67 Positive, 233 Negative)
- **Data Integrity Verification**: `python scripts/verify_test_set.py` $\rightarrow$ **PASS**
