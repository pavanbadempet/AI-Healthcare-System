"""
Unit tests for SOTA PQC & ZKP Engine (backend/sota_pqc_zkp_layer.py).
"""

from backend.sota_pqc_zkp_layer import SOTAPQCZKPLayerEngine


def test_quantum_safe_key_encapsulation_and_zkp_verification():
    engine = SOTAPQCZKPLayerEngine()

    pk = b"PUBLIC_KEY_SAMPLE_12345"
    encapsulation = engine.encapsulate_quantum_safe_key(pk)

    assert encapsulation.algorithm == "KYBER_1024_PQC_LATTICE"
    assert encapsulation.is_quantum_safe
    assert encapsulation.shared_secret_bytes_len == 32

    proof = b"PROOF_BYTES_SAMPLE"
    pub_in = b"PUBLIC_INPUTS_SAMPLE"
    zk_result = engine.verify_zero_knowledge_claim(proof, pub_in)

    assert zk_result.proof_type == "ZK_SNARK_GROTH16"
    assert zk_result.claim_verified
    assert zk_result.is_zero_knowledge
    assert zk_result.verification_time_us >= 0.0
