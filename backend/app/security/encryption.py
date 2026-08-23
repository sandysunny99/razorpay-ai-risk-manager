import os
import base64
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.security.key_provider import key_provider

class FieldEncryptionEngine:
    """
    AES-256-GCM Authenticated Encryption for sensitive database fields.
    Guarantees confidentiality, integrity, and nonce uniqueness.
    """
    ALGORITHM = "AES-256-GCM"

    @classmethod
    def encrypt(cls, plaintext: str, key_version: Optional[str] = None) -> Dict[str, str]:
        """
        Encrypts plaintext string with AES-256-GCM using active or specified key version.
        Returns structured payload containing base64 ciphertext, nonce, and key version.
        """
        if not plaintext:
            return {"ciphertext": "", "nonce": "", "key_version": "v1", "algorithm": cls.ALGORITHM}

        if key_version:
            key_entry = key_provider.get_key_by_version(key_version)
        else:
            key_entry = key_provider.get_active_key()

        if not key_entry or key_entry.get("status") == "REVOKED":
            raise ValueError(f"Encryption key version '{key_version}' is invalid or revoked.")

        key_bytes = key_entry["key_bytes"]
        aesgcm = AESGCM(key_bytes)
        
        # 96-bit unique nonce as recommended by NIST SP 800-38D
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

        return {
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "key_version": key_entry["version"],
            "algorithm": cls.ALGORITHM
        }

    @classmethod
    def decrypt(cls, payload: Dict[str, str]) -> str:
        """
        Decrypts structured ciphertext payload with authenticated integrity check.
        Raises ValueError if tag mismatch, tampering, or unknown key version is detected.
        """
        ciphertext_b64 = payload.get("ciphertext")
        nonce_b64 = payload.get("nonce")
        key_ver = payload.get("key_version", "v1")

        if not ciphertext_b64 or not nonce_b64:
            return ""

        key_entry = key_provider.get_key_by_version(key_ver)
        if not key_entry:
            raise ValueError(f"Unknown encryption key version: {key_ver}")
        if key_entry.get("status") == "REVOKED":
            raise ValueError(f"Cannot decrypt with REVOKED key version: {key_ver}")

        key_bytes = key_entry["key_bytes"]
        aesgcm = AESGCM(key_bytes)

        try:
            nonce = base64.b64decode(nonce_b64)
            ciphertext = base64.b64decode(ciphertext_b64)
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Decryption failed: Ciphertext tampered or invalid key/tag ({str(e)})")
