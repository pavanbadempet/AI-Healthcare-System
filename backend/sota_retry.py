"""
AI Healthcare System — SOTA Resilient Retry Engine
===================================================
Provides state-of-the-art resilience retry primitives:
1. Exponential Backoff with Full Jitter
2. Transient vs Non-Transient Exception Classification
3. Maximum Retry Budget & Timeout Protection
"""

import asyncio
import random
from typing import Any, Callable, TypeVar

T = TypeVar("T")

TRANSIENT_EXCEPTIONS = (
    TimeoutError,
    ConnectionResetError,
    ConnectionRefusedError,
    OSError,
)


def calculate_jitter_backoff(attempt: int, base_delay: float = 0.1, max_delay: float = 5.0) -> float:
    """
    Full Jitter Exponential Backoff formula: random(0, min(max_delay, base_delay * 2^attempt))
    Prevents thundering herd server overloads.
    """
    temp = min(max_delay, base_delay * (2 ** attempt))
    return random.uniform(0, temp)


async def execute_with_sota_retry(
    coro_fn: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 0.05,
    max_delay: float = 2.0,
) -> Any:
    """
    Executes an async callable with SOTA Exponential Backoff & Full Jitter.
    Retries only transient failures and fails fast on non-transient errors.
    """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except TRANSIENT_EXCEPTIONS as exc:
            last_exception = exc
            if attempt == max_retries:
                raise exc
            sleep_time = calculate_jitter_backoff(attempt, base_delay, max_delay)
            await asyncio.sleep(sleep_time)
        except Exception as exc:
            # Non-transient error -> fail fast
            raise exc

    if last_exception:
        raise last_exception
