"""Tests for Frontier Cryptographic Security and Post-Quantum Privacy Suite.

Verifies:
1. Ciphertext-Policy Attribute-Based Encryption (CP-ABE) zero-trust field encryption.
2. Ring-LWE Fully Homomorphic Encryption (FHE) encrypted clinical risk inference.
3. NIST ML-KEM-1024 (Kyber-1024) + X25519 hybrid quantum-resistant key encapsulation.
4. Forward-Secure Merkle Audit Logging with cryptographic epoch key ratchets.
5. FastAPI /v1/security-privacy endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.security_privacy.cp_abe_engine import (
    AccessDeniedCryptographicPolicyError,
    CpAbeAuthority,
    PolicySyntaxError,
    ShamirSecretSharing,
)
from backend.security_privacy.forward_secure_audit import (
    ForwardSecureAuditLog,
)
from backend.security_privacy.homomorphic_inference import (
    EncryptedClinicalRiskPredictor,
    HomomorphicContext,
)
from backend.security_privacy.post_quantum_crypto import (
    PostQuantumKemEngine,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# =========================================================================
# 1. Ciphertext-Policy Attribute-Based Encryption (CP-ABE) Tests
# =========================================================================

def test_shamir_secret_sharing_reconstruction():
    """Verify (k, n) threshold secret sharing and Lagrange polynomial interpolation."""
    secret = 0xDEADBEEFCAFE1234
    k = 3
    n = 5

    shares = ShamirSecretSharing.split_secret(secret, threshold=k, total_shares=n)
    assert len(shares) == n

    # Reconstructing with exact threshold k should recover secret
    recovered_exact = ShamirSecretSharing.reconstruct_secret(shares[:k])
    assert recovered_exact == secret

    # Reconstructing with all n shares should recover secret
    recovered_all = ShamirSecretSharing.reconstruct_secret(shares)
    assert recovered_all == secret

    # Any k shares (e.g. indices 0, 2, 4) should recover secret
    subset_shares = [shares[0], shares[2], shares[4]]
    recovered_subset = ShamirSecretSharing.reconstruct_secret(subset_shares)
    assert recovered_subset == secret

    # Fewer than k shares must fail
    with pytest.raises(ValueError, match="Requires at least"):
        ShamirSecretSharing.reconstruct_secret(shares[: k - 1])


def test_cp_abe_encryption_satisfaction_and_denial():
    """Verify access policy satisfaction logic and mathematical denial."""
    authority = CpAbeAuthority()
    policy = "(ROLE:ONCOLOGIST AND DEPT:CANCER_CARE) OR USER_ID:P-101"
    clinical_data = {
        "patient_id": "PT-9801",
        "genomic_variant": "TP53 c.743G>A",
        "chemotherapy_regimen": "FOLFOX6-modified",
        "dosage_mg": 400,
    }

    envelope = authority.encrypt_data(clinical_data, policy)
    assert envelope.policy_str == policy
    assert envelope.ciphertext_b64 is not None

    # Case 1: Satisfying user with (ROLE:ONCOLOGIST AND DEPT:CANCER_CARE)
    oncologist_key = authority.generate_user_private_key(
        user_id="dr_smith",
        user_attributes={"ROLE:ONCOLOGIST", "DEPT:CANCER_CARE", "HOSPITAL:MEMORIAL"},
    )
    decrypted_oncologist = authority.decrypt_data(envelope, oncologist_key)
    assert decrypted_oncologist == clinical_data

    # Case 2: Satisfying user with USER_ID:P-101
    patient_key = authority.generate_user_private_key(
        user_id="patient_101",
        user_attributes={"USER_ID:P-101", "PORTAL:PATIENT_ACCESS"},
    )
    decrypted_patient = authority.decrypt_data(envelope, patient_key)
    assert decrypted_patient == clinical_data

    # Case 3: Non-satisfying user (only ONCOLOGIST without DEPT:CANCER_CARE)
    nurse_key = authority.generate_user_private_key(
        user_id="nurse_kelly",
        user_attributes={"ROLE:ONCOLOGIST", "DEPT:CARDIOLOGY"},
    )
    with pytest.raises(AccessDeniedCryptographicPolicyError, match="satisfy policy"):
        authority.decrypt_data(envelope, nurse_key)

    # Case 4: Completely disjoint attributes
    billing_key = authority.generate_user_private_key(
        user_id="billing_clerk",
        user_attributes={"ROLE:BILLING", "DEPT:FINANCE"},
    )
    with pytest.raises(AccessDeniedCryptographicPolicyError):
        authority.decrypt_data(envelope, billing_key)


def test_cp_abe_policy_syntax_error():
    """Verify parser rejects malformed boolean logic."""
    authority = CpAbeAuthority()
    with pytest.raises(PolicySyntaxError):
        authority.encrypt_data({"k": "v"}, "ROLE:ONCOLOGIST AND AND DEPT:CLINIC")


# =========================================================================
# 2. Fully Homomorphic Encryption (FHE) Risk Inference Tests
# =========================================================================

def test_ring_lwe_homomorphic_addition_and_multiplication():
    """Verify homomorphic ciphertext addition and scalar multiplication."""
    ctx = HomomorphicContext(dimension=256, scale=1000)
    pk, sk = ctx.keygen()

    vec_a = [10.0, -5.0, 3.5]
    vec_b = [2.0, 7.5, -1.0]

    c_a = ctx.encrypt_vector(vec_a, pk)
    c_b = ctx.encrypt_vector(vec_b, pk)

    # Homomorphic addition: c_sum = c_a + c_b
    c_sum = ctx.homomorphic_add(c_a, c_b)
    decrypted_sum = ctx.decrypt_vector(c_sum, sk, length=len(vec_a))

    for original_a, original_b, dec in zip(vec_a, vec_b, decrypted_sum):
        expected = original_a + original_b
        assert abs(dec - expected) < 0.25, f"Expected {expected}, got {dec}"

    # Homomorphic scalar multiplication: c_scaled = c_a * 3.0
    c_scaled = ctx.homomorphic_multiply_plain(c_a, 3.0)
    decrypted_scaled = ctx.decrypt_vector(c_scaled, sk, length=len(vec_a))

    for original_a, dec in zip(vec_a, decrypted_scaled):
        expected = original_a * 3.0
        assert abs(dec - expected) < 0.25, f"Expected {expected}, got {dec}"


def test_encrypted_ascvd_risk_scoring():
    """Verify end-to-end homomorphic evaluation of ASCVD cardiovascular risk."""
    predictor = EncryptedClinicalRiskPredictor()
    pk, sk = predictor.context.keygen()

    # Patient vitals: [age=65, sbp=160, chol=240, hdl=35, smoker=1, diabetes=1]
    vitals = [65.0, 160.0, 240.0, 35.0, 1.0, 1.0]

    # Plaintext expectation
    plaintext_risk = predictor.evaluate_plaintext(vitals)
    assert 0.0 <= plaintext_risk <= 1.0

    # Encrypted risk evaluation (server side, zero plaintext knowledge)
    encrypted_vitals = predictor.encrypt_patient_vitals(vitals, pk)
    encrypted_result = predictor.evaluate_encrypted_ascvd(encrypted_vitals)

    # Decrypt at client
    decrypted_risk = predictor.decrypt_risk_score(encrypted_result, sk)

    # Verifying homomorphic prediction numerical convergence
    assert abs(decrypted_risk - plaintext_risk) <= 0.05, (
        f"Homomorphic risk {decrypted_risk:.4f} deviated from plaintext {plaintext_risk:.4f}"
    )


# =========================================================================
# 3. Post-Quantum Cryptography (ML-KEM Kyber-1024 + X25519) Tests
# =========================================================================

def test_pqc_hybrid_kem_exchange():
    """Verify ML-KEM-1024 + X25519 hybrid quantum-resistant key agreement."""
    engine = PostQuantumKemEngine()

    # Recipient generates keypair
    pk, sk = engine.generate_keypair()
    assert pk.algorithm == "ML-KEM-1024+X25519"

    # Sender encapsulates shared secret
    ciphertext, sender_shared_secret = engine.encapsulate(pk)
    assert len(sender_shared_secret) == 32
    assert ciphertext.kem_ciphertext is not None
    assert ciphertext.classical_ephemeral_pk is not None

    # Recipient decapsulates
    recipient_shared_secret = engine.decapsulate(ciphertext, sk)
    assert len(recipient_shared_secret) == 32

    # Both parties derive identical 256-bit symmetric key
    assert sender_shared_secret == recipient_shared_secret


def test_pqc_tamper_rejection():
    """Verify Fujisaki-Okamoto transform rejects tampered quantum ciphertexts."""
    engine = PostQuantumKemEngine()
    pk, sk = engine.generate_keypair()
    ciphertext, legitimate_secret = engine.encapsulate(pk)

    # Tamper with the ciphertext bytes
    tampered_raw = list(ciphertext.kem_ciphertext)
    tampered_raw[10] ^= 0xFF
    ciphertext.kem_ciphertext = bytes(tampered_raw)

    # Decapsulation with tampered ciphertext will produce a pseudo-random divergent secret
    tampered_secret = engine.decapsulate(ciphertext, sk)
    assert tampered_secret != legitimate_secret


# =========================================================================
# 4. Forward-Secure Merkle Audit Logging Tests
# =========================================================================

def test_forward_secure_audit_chain_and_epoch_ratchet():
    """Verify monotonic epoch ratcheting and Merkle DAG integrity."""
    audit = ForwardSecureAuditLog()

    # Epoch 0: Record 3 actions
    e1 = audit.record_entry("dr_alice", "VIEW_CHART", "PT-100", {"dept": "ICU"})
    e2 = audit.record_entry("nurse_bob", "ADMINISTER_MED", "PT-100", {"med": "Heparin"})
    e3 = audit.record_entry("dr_alice", "UPDATE_DIAGNOSIS", "PT-100", {"code": "I21.9"})

    assert e1.epoch == 0
    assert e2.epoch == 0
    assert e3.epoch == 0
    assert e2.prev_hash == e1.entry_hash
    assert e3.prev_hash == e2.entry_hash

    is_valid, msg, violations = audit.verify_chain_integrity()
    assert is_valid is True
    assert len(violations) == 0

    # Advance to Epoch 1 (irrevocable forward ratchet)
    new_epoch = audit.advance_epoch()
    assert new_epoch == 1

    # Epoch 1: Record another action
    e4 = audit.record_entry("dr_charlie", "CONSULT_NOTE", "PT-100", {"note": "Stable"})
    assert e4.epoch == 1
    assert e4.prev_hash == e3.entry_hash

    # Full chain verification across epochs
    is_valid_after_ratchet, _, violations_after = audit.verify_chain_integrity()
    assert is_valid_after_ratchet is True
    assert len(violations_after) == 0


def test_forward_secure_audit_tamper_detection():
    """Verify log tampering in prior epochs is immediately flagged."""
    audit = ForwardSecureAuditLog()
    audit.record_entry("dr_alice", "ACCESS_EHR", "PT-200", {"status": "ok"})
    audit.record_entry("dr_bob", "PRESCRIBE", "PT-200", {"rx": "Amoxicillin"})

    audit.advance_epoch()

    # Tamper with the details of the first entry
    audit.entries[0].details["status"] = "tampered_by_adversary"

    is_valid, msg, violations = audit.verify_chain_integrity()
    assert is_valid is False
    assert len(violations) > 0


# =========================================================================
# 5. FastAPI /v1/security-privacy Route Integration Tests
# =========================================================================

def test_route_security_privacy_health(client: TestClient):
    """Verify health endpoint reporting status of all 4 cryptographic suites."""
    resp = client.get("/v1/security-privacy/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert "cp_abe" in data
    assert "fhe" in data
    assert "pqc" in data
    assert "audit" in data


def test_route_cp_abe_encrypt_and_decrypt(client: TestClient):
    """Verify CP-ABE HTTP endpoint encrypt/decrypt lifecycle."""
    payload = {
        "policy": "(ROLE:CHIEF_MEDICAL_OFFICER AND CLEARANCE:LEVEL_3) OR USER:DIRECTOR",
        "data": {
            "trial_id": "ONCO-PHASE-3-009",
            "blinded_code": "V-9921",
            "efficacy_index": 0.884,
        },
    }

    # Encrypt
    enc_resp = client.post("/v1/security-privacy/cp-abe/encrypt", json=payload)
    assert enc_resp.status_code == 200
    enc_data = enc_resp.json()
    assert "envelope" in enc_data
    assert enc_data["policy_parsed"]["type"] == "OR"

    envelope = enc_data["envelope"]

    # Decrypt with satisfying attributes
    dec_req_success = {
        "envelope": envelope,
        "user_id": "cmo_jones",
        "user_attributes": ["ROLE:CHIEF_MEDICAL_OFFICER", "CLEARANCE:LEVEL_3"],
    }
    dec_resp_success = client.post("/v1/security-privacy/cp-abe/decrypt", json=dec_req_success)
    assert dec_resp_success.status_code == 200
    assert dec_resp_success.json()["decrypted_data"] == payload["data"]

    # Decrypt with non-satisfying attributes
    dec_req_fail = {
        "envelope": envelope,
        "user_id": "intern_dave",
        "user_attributes": ["ROLE:INTERN", "CLEARANCE:LEVEL_1"],
    }
    dec_resp_fail = client.post("/v1/security-privacy/cp-abe/decrypt", json=dec_req_fail)
    assert dec_resp_fail.status_code == 403
    assert "Access Denied" in dec_resp_fail.json()["detail"]


def test_route_fhe_evaluate_risk(client: TestClient):
    """Verify homomorphic ASCVD risk prediction over HTTP."""
    ctx = HomomorphicContext()
    pk, sk = ctx.keygen()

    vitals = [58.0, 145.0, 220.0, 42.0, 0.0, 1.0]
    predictor = EncryptedClinicalRiskPredictor(context=ctx)
    encrypted_vitals = predictor.encrypt_patient_vitals(vitals, pk)

    req_body = {
        "encrypted_vitals": [c.to_dict() for c in encrypted_vitals],
        "patient_id": "PT-CONFIDENTIAL-01",
    }

    resp = client.post("/v1/security-privacy/fhe/evaluate-risk", json=req_body)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "COMPLETED"
    assert res_data["privacy_guarantee"] == "Zero-Knowledge Ciphertext Arithmetic (Ring-LWE)"

    # Client decrypts returned ciphertext
    from backend.security_privacy.homomorphic_inference import FheCiphertext
    res_ct = FheCiphertext.from_dict(res_data["encrypted_risk_result"])
    decrypted_risk = predictor.decrypt_risk_score(res_ct, sk)
    assert 0.0 <= decrypted_risk <= 1.0


def test_route_pqc_hybrid_kem_exchange(client: TestClient):
    """Verify ML-KEM-1024 hybrid post-quantum exchange endpoint."""
    resp = client.post("/v1/security-privacy/pqc/hybrid-kem-exchange")
    assert resp.status_code == 200
    data = resp.json()
    assert data["quantum_resistant_algorithm"] == "ML-KEM-1024 (NIST FIPS 203)"
    assert data["classical_algorithm"] == "X25519 (RFC 7748)"
    assert data["status"] == "KEY_EXCHANGE_SUCCESS"
    assert len(data["shared_secret_hex"]) == 64  # 32 bytes hex


def test_route_forward_secure_audit_lifecycle(client: TestClient):
    """Verify audit logging, epoch advance, and verification endpoints."""
    # 1. Log event
    log_req = {
        "actor": "clinician_44",
        "action": "EXPORT_GENOMIC_PROFILE",
        "patient_id": "PT-GEN-88",
        "details": {"genome_size_mb": 3200},
    }
    resp_log = client.post("/v1/security-privacy/audit/forward-secure-log", json=log_req)
    assert resp_log.status_code == 200
    log_data = resp_log.json()
    assert log_data["chain_valid"] is True
    assert log_data["entry"]["actor"] == "clinician_44"

    # 2. Advance epoch
    resp_epoch = client.post("/v1/security-privacy/audit/advance-epoch")
    assert resp_epoch.status_code == 200
    assert resp_epoch.json()["new_epoch"] >= 1

    # 3. Verify audit log
    resp_verify = client.get("/v1/security-privacy/audit/verify")
    assert resp_verify.status_code == 200
    verify_data = resp_verify.json()
    assert verify_data["valid"] is True
    assert verify_data["status"] == "CHAIN_VERIFIED_INTEGRITY_INTACT"
    assert len(verify_data["violations"]) == 0
