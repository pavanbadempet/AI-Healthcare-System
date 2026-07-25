"""
Unit tests for SOTA Rust Engine (backend/sota_rust_engine_layer.py).
"""

from backend.sota_rust_engine_layer import SOTARustEngineLayerEngine


def test_rust_cosine_similarity_computation():
    engine = SOTARustEngineLayerEngine()

    v1 = [1.0, 0.0, 1.0]
    v2 = [1.0, 0.0, 1.0]

    metrics = engine.compute_rust_cosine_similarity(v1, v2)

    assert metrics.task_name == "RUST_PYO3_COSINE_SIMILARITY"
    assert metrics.vector_dim == 3
    assert metrics.result == 1.0
    assert metrics.is_rust_native
    assert metrics.execution_time_us >= 0.0
