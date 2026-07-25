"""
Unit tests for SOTA Circuit Breaker Engine (backend/sota_circuit_breaker_layer.py).
"""

from backend.sota_circuit_breaker_layer import SOTACircuitBreakerLayerEngine


def test_circuit_breaker_state_transitions():
    engine = SOTACircuitBreakerLayerEngine()

    s1 = engine.execute_with_circuit_breaker("PACS_SERVICE", primary_action_success=True)
    assert s1.state == "CLOSED"
    assert not s1.fallback_executed

    engine.execute_with_circuit_breaker("PACS_SERVICE", primary_action_success=False)
    engine.execute_with_circuit_breaker("PACS_SERVICE", primary_action_success=False)
    s3 = engine.execute_with_circuit_breaker("PACS_SERVICE", primary_action_success=False)

    assert s3.state == "OPEN"
    assert s3.fallback_executed
    assert s3.execution_time_ms >= 0.0
