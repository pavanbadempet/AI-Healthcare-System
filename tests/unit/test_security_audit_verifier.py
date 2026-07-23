"""
Unit tests for Cryptographic Audit Hash Chain Verifier
"""

import pytest
from backend.security_audit_verifier import AuditHashChainVerifier, audit_verifier


def test_verify_hash_chain_valid():
    h1 = audit_verifier.compute_record_hash(1, "LOGIN", "User login", "0" * 64)
    h2 = audit_verifier.compute_record_hash(2, "VIEW_RECORD", "Viewed record", h1)

    logs = [
        {"id": 1, "action": "LOGIN", "details": "User login", "hash": h1},
        {"id": 2, "action": "VIEW_RECORD", "details": "Viewed record", "hash": h2},
    ]

    res = audit_verifier.verify_hash_chain(logs)
    assert res["chain_valid"] is True
    assert res["status"] == "VERIFIED_TAMPER_EVIDENT"


def test_verify_hash_chain_tampered():
    h1 = audit_verifier.compute_record_hash(1, "LOGIN", "User login", "0" * 64)
    h2 = audit_verifier.compute_record_hash(2, "VIEW_RECORD", "Viewed record", h1)

    logs = [
        {"id": 1, "action": "LOGIN", "details": "User login TAMPERED", "hash": h1},
        {"id": 2, "action": "VIEW_RECORD", "details": "Viewed record", "hash": h2},
    ]

    res = audit_verifier.verify_hash_chain(logs)
    assert res["chain_valid"] is False
    assert res["status"] == "CORRUPTED_HASH_CHAIN"
