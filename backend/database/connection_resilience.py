"""
Database connection pool resilience with exponential jittered backoff.
"""
import asyncio
import random
from typing import Callable, TypeVar

T = TypeVar("T")

async def retry_with_backoff(operation: Callable[[], T], max_retries: int = 5, base_delay: float = 0.5) -> T:
    """Execute asynchronous database operation with full jitter exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
            await asyncio.sleep(delay)
