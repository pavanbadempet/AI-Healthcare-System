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
