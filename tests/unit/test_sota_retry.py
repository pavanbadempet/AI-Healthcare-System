"""
Unit tests for SOTA Resilient Retry Engine (backend/sota_retry.py).
"""

import pytest

from backend.sota_retry import calculate_jitter_backoff, execute_with_sota_retry


def test_jitter_backoff_bounds():
    for attempt in range(5):
        delay = calculate_jitter_backoff(attempt, base_delay=0.1, max_delay=1.0)
        assert 0 <= delay <= 1.0


@pytest.mark.asyncio
async def test_successful_retry():
    calls = 0

    async def flaky_task():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionResetError("Transient network glitch")
        return "SUCCESS"

    result = await execute_with_sota_retry(flaky_task, max_retries=3, base_delay=0.01)
    assert result == "SUCCESS"
    assert calls == 3


@pytest.mark.asyncio
async def test_fail_fast_non_transient():
    async def bad_task():
        raise ValueError("Invalid parameter value")

    with pytest.raises(ValueError, match="Invalid parameter value"):
        await execute_with_sota_retry(bad_task, max_retries=3)
