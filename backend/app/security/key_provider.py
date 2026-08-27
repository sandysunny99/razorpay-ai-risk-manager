import os
import hashlib
from typing import Dict, Optional
from datetime import datetime, timezone

class KeyProvider:
    """Abstract interface for cryptographic key management."""
    def get_active_key(self) -> Dict[str, str]:
        raise NotImplementedError

    def get_key_by_version(self, version: str) -> Optional[Dict[str, str]]:
        raise NotImplementedError

    def rotate_key(self, new_key_material: Optional[str] = None) -> Dict[str, str]:
        raise NotImplementedError

class EnvironmentKeyProvider(KeyProvider):
    """
    Manages versioned AES-256 and HMAC cryptographic keys from environment/KMS.
    Never exposes raw key material in logs or unauthenticated responses.
    """
    def __init__(self):
        # Derive primary 256-bit key from environment or deterministic secure seed
        seed = os.getenv("MASTER_ENCRYPTION_KEY", "razorpay_risk_agent_master_aes256_gcm_secret_key_2026")
        self._keys: Dict[str, Dict[str, str]] = {
            "v1": {
                "key_id": "key_v1_primary",
                "version": "v1",
                "key_bytes": hashlib.sha256(seed.encode("utf-8")).digest(),
                "status": "ACTIVE",
                "created_at": "2026-08-01T00:00:00Z"
            }
        }
        self._active_version = "v1"

    def get_active_key(self) -> Dict[str, str]:
        return self._keys[self._active_version]

    def get_key_by_version(self, version: str) -> Optional[Dict[str, str]]:
        return self._keys.get(version)

    def rotate_key(self, new_key_material: Optional[str] = None) -> Dict[str, str]:
        old_version = self._active_version
        new_version_num = int(old_version.replace("v", "")) + 1
        new_version = f"v{new_version_num}"
        
        # Mark previous key as RETIRED (still readable for old ciphertexts)
        if old_version in self._keys:
            self._keys[old_version]["status"] = "RETIRED"
            
        seed = new_key_material or f"razorpay_risk_agent_key_rotation_{new_version}_{datetime.now(timezone.utc).isoformat()}"
        self._keys[new_version] = {
            "key_id": f"key_{new_version}_rotated",
            "version": new_version,
            "key_bytes": hashlib.sha256(seed.encode("utf-8")).digest(),
            "status": "ACTIVE",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._active_version = new_version
        return self._keys[new_version]

    def get_all_key_metadata(self) -> list:
        """Returns safe metadata without exposing raw key bytes."""
        return [
            {
                "key_id": k["key_id"],
                "version": k["version"],
                "status": k["status"],
                "created_at": k["created_at"],
                "algorithm": "AES-256-GCM"
            }
            for k in self._keys.values()
        ]

# Global singleton
key_provider = EnvironmentKeyProvider()
