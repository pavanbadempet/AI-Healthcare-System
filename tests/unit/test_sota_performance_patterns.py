"""
Unit tests for SOTA Performance Design Patterns (backend/performance.py).
"""

import pytest
import asyncio
from backend.performance import fast_json_dumps, fast_json_loads, gather_concurrent_tasks, IndexedLookupCache


def test_fast_json_dumps_and_loads():
    payload = {"patient_id": 101, "name": "John Doe", "metrics": [120, 80]}
    encoded = fast_json_dumps(payload)
    assert isinstance(encoded, str)
    decoded = fast_json_loads(encoded)
    assert decoded == payload


@pytest.mark.asyncio
async def test_gather_concurrent_tasks():
    async def task_a():
        await asyncio.sleep(0.01)
        return "result_a"

    async def task_b():
        await asyncio.sleep(0.01)
        return "result_b"

    results = await gather_concurrent_tasks(task_a(), task_b())
    assert results == ["result_a", "result_b"]


def test_indexed_lookup_cache():
    patients = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"}
    ]
    cache = IndexedLookupCache(patients, key_field="id")
    assert len(cache) == 3
    assert cache.get(2) == {"id": 2, "name": "Bob"}
    assert cache.get(99) is None
    assert cache.contains(1) is True
