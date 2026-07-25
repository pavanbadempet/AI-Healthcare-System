"""
Unit tests for SOTA Fast Programming Language Engine (backend/sota_fast_programming_language_layer.py).
"""

from backend.sota_fast_programming_language_layer import SOTAFastProgrammingLanguageLayerEngine


def test_native_vector_sum_execution():
    engine = SOTAFastProgrammingLanguageLayerEngine()

    vec = [1.5, 2.5, 3.5, 4.5, 5.5]
    result = engine.execute_native_vector_sum(vec)

    assert result.input_vector_size == 5
    assert result.sum_result == 17.5
    assert result.is_simd_accelerated
    assert result.execution_time_us >= 0.0
