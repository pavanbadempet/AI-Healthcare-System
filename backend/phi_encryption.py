"""PHI Field Encryption — HIPAA-compliant encryption at rest.

Provides Fernet symmetric encryption for Protected Health Information fields.
Requires PHI_ENCRYPTION_KEY environment variable in production.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_fernet = None
_encryption_available = False

def _initialize_encryption() -> None:
    global _fernet, _encryption_available
    key = os.getenv("PHI_ENCRYPTION_KEY")
    if not key:
        if not os.getenv("TESTING"):
            logger.warning(
                "PHI_ENCRYPTION_KEY not set. PHI field encryption is DISABLED. "
                "Set this variable before handling production patient data."
            )
        _encryption_available = False
        return
    try:
        from cryptography.fernet import Fernet
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
        _encryption_available = True
        logger.info("PHI field encryption initialized successfully.")
    except Exception as e:
        logger.error("Failed to initialize PHI encryption: %s", e)
        _encryption_available = False

_initialize_encryption()

def is_encryption_available() -> bool:
    return _encryption_available

def encrypt_phi(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    if not _encryption_available or _fernet is None:
        return plaintext
    try:
        return _fernet.encrypt(plaintext.encode()).decode()
    except Exception as e:
        logger.error("PHI encryption failed: %s", e)
        return plaintext

def decrypt_phi(ciphertext: str) -> str:
    if not ciphertext:
        return ciphertext
    if not _encryption_available or _fernet is None:
        return ciphertext
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except Exception:
        # May be unencrypted legacy data — return as-is
        return ciphertext

def generate_encryption_key() -> str:
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()

def get_encryption_status() -> dict:
    return {
        "phi_encryption_enabled": _encryption_available,
        "key_configured": bool(os.getenv("PHI_ENCRYPTION_KEY")),
        "algorithm": "Fernet (AES-128-CBC + HMAC-SHA256)" if _encryption_available else "none",
    }
