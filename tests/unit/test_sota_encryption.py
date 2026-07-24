"""
Unit tests for SOTA AES-256-GCM Cryptographic Engine (backend/sota_encryption.py).
"""

import os

import pytest

from backend.sota_encryption import SOTAEncryptionEngine


def test_encryption_decryption_cycle():
    engine = SOTAEncryptionEngine()
    master_key = b"SUPER_SECRET_HEALTHCARE_MASTER_KEY_32B"
    salt = os.urandom(16)

    key_256 = engine.derive_key(master_key, salt)
    assert len(key_256) == 32

    raw_text = b"PATIENT_PHI_RECORD_DATA_CONFIDENTIAL"
    encrypted = engine.encrypt_payload(raw_text, key_256)
    assert encrypted != raw_text

    decrypted = engine.decrypt_payload(encrypted, key_256)
    assert decrypted == raw_text


def test_tamper_verification_failure():
    engine = SOTAEncryptionEngine()
    key_256 = os.urandom(32)

    encrypted = engine.encrypt_payload(b"CONFIDENTIAL_DATA", key_256)
    # Corrupt ciphertext byte
    tampered = bytearray(encrypted)
    tampered[-1] ^= 0xFF

    with pytest.raises(Exception):
        engine.decrypt_payload(bytes(tampered), key_256)
