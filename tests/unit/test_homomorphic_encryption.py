"""
Unit tests for Homomorphic Encryption Engine
"""

from backend.security.homomorphic_encryption_engine import homomorphic_engine


def test_encrypt_and_evaluate():
    encrypted = homomorphic_engine.encrypt_vector([120.0, 80.0, 75.0], key_size_bits=2048)
    assert encrypted["status"] == "ENCRYPTED"
    assert len(encrypted["ciphertexts"]) == 3

    evaluated = homomorphic_engine.evaluate_encrypted_risk_score(encrypted)
    assert evaluated["status"] == "EVALUATION_SUCCESS"
    assert evaluated["privacy_guarantee"] == "ZERO_PLAINTEXT_MEMORY_EXPOSURE"
