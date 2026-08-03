"""
Unit tests for Rust Native Execution Engine and Clinical Score Calculator.
"""

from backend.sota_rust_engine_layer import sota_rust_engine_layer_engine


def test_rust_engine_cosine_similarity():
    vec_a = [1.0, 2.0, 3.0]
    vec_b = [1.0, 2.0, 3.0]
    res = sota_rust_engine_layer_engine.compute_rust_cosine_similarity(vec_a, vec_b)
    assert res.result == 1.0
    assert res.vector_dim == 3
    assert res.is_rust_native is True

def test_rust_engine_egfr_calculation():
    # Female patient, Cr 0.9, Age 45
    egfr = sota_rust_engine_layer_engine.compute_rust_egfr(0.9, 45, is_female=True)
    assert egfr > 80.0
    assert egfr < 120.0

def test_rust_phi_redaction():
    text = "Patient SSN is 123-45-6789 and contact is john.doe@hospital.org"
    redacted = sota_rust_engine_layer_engine.redact_phi_text_rust(text)
    assert "123-45-6789" not in redacted
    assert "john.doe@hospital.org" not in redacted
    assert "[REDACTED-SSN]" in redacted
    assert "[REDACTED-EMAIL]" in redacted

def test_rust_password_hashing():
    pwd = "SecureClinicalPassword123!"
    hashed = sota_rust_engine_layer_engine.hash_password_rust(pwd)
    assert hashed != pwd
    assert sota_rust_engine_layer_engine.verify_password_rust(pwd, hashed) is True
    assert sota_rust_engine_layer_engine.verify_password_rust("WrongPassword", hashed) is False

def test_rust_fedavg_aggregation():
    grads = [[1.0, 2.0], [3.0, 4.0]]
    weights = [0.5, 0.5]
    result = sota_rust_engine_layer_engine.aggregate_fedavg_rust(grads, weights)
    assert result == [2.0, 3.0]
