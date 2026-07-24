"""
Unit tests for Advanced SOTA Behavioral Design Patterns (backend/sota_patterns.py).
"""

import asyncio

import pytest

from backend.sota_patterns import BulkheadIsolation, CircuitBreaker, CircuitState, CQRSReadCache


def test_circuit_breaker_normal_operation():
    cb = CircuitBreaker(failure_threshold=3)
    res = cb.call(lambda x: x * 2, 5)
    assert res == 10
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_tripping():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=60.0)

    def failing_func():
        raise ValueError("API Error")

    with pytest.raises(ValueError):
        cb.call(failing_func)

    with pytest.raises(ValueError):
        cb.call(failing_func)

    assert cb.state == CircuitState.OPEN

    with pytest.raises(RuntimeError) as exc_info:
        cb.call(failing_func)
    assert "CircuitBreaker is OPEN" in str(exc_info.value)


@pytest.mark.asyncio
async def test_bulkhead_isolation():
    bulkhead = BulkheadIsolation(max_concurrent=2)

    async def dummy_work(val):
        await asyncio.sleep(0.01)
        return val * 10

    res = await bulkhead.execute(dummy_work, 4)
    assert res == 40


def test_cqrs_read_cache():
    cache = CQRSReadCache()
    cache.update_read_model("patient_123", {"name": "Alice", "status": "admitted"})

    record = cache.query_read_model("patient_123")
    assert record["name"] == "Alice"
    assert record["status"] == "admitted"
    assert "_updated_at" in record

    cache.invalidate("patient_123")
    assert cache.query_read_model("patient_123") is None
