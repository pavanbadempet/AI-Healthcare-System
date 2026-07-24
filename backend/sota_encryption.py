"""
AI Healthcare System — SOTA AES-256-GCM Cryptographic Engine
============================================================
Provides state-of-the-art authenticated encryption (AEAD):
1. AES-256-GCM authenticated payload encryption & decryption
2. HKDF-SHA256 key derivation
3. Cryptographically random 96-bit nonces
"""

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class SOTAEncryptionEngine:
    """AES-256-GCM Authenticated Encryption & Key Derivation Processor."""

    def derive_key(self, master_key: bytes, salt: bytes, info: bytes = b"healthcare_phi_v1") -> bytes:
        """Derives a 256-bit cryptographic key using HKDF-SHA256."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=info,
        )
        return hkdf.derive(master_key)

    def encrypt_payload(self, raw_data: bytes, key_256: bytes) -> bytes:
        """
        Encrypts raw payload using AES-256-GCM.
        Returns nonce (12 bytes) + ciphertext + authentication tag.
        """
        aesgcm = AESGCM(key_256)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, raw_data, None)
        return nonce + ciphertext

    def decrypt_payload(self, encrypted_payload: bytes, key_256: bytes) -> bytes:
        """
        Decrypts AES-256-GCM payload and verifies integrity tag.
        """
        if len(encrypted_payload) < 12:
            raise ValueError("Invalid ciphertext payload length")

        nonce = encrypted_payload[:12]
        ciphertext = encrypted_payload[12:]
        aesgcm = AESGCM(key_256)
        return aesgcm.decrypt(nonce, ciphertext, None)


sota_crypto_engine = SOTAEncryptionEngine()
