import functools
import logging
from typing import Callable, Any, TypeVar

T = TypeVar('T')

class NoLogZone:
    """Context manager that temporarily disables all application logging to prevent data leakage."""
    def __init__(self):
        self.root_logger = logging.getLogger()
        self.previous_level = self.root_logger.level
        self.disabled_level = logging.CRITICAL + 1 # Higher than any level, basically turns it off

    def __enter__(self):
        self.root_logger.setLevel(self.disabled_level)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.root_logger.setLevel(self.previous_level)

def no_log_zone(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to wrap sensitive clinical prediction functions.
    Temporarily suppresses all application logs (logger.info, logger.debug) 
    during the function's execution to guarantee zero data leakage in server logs.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        with NoLogZone():
            return func(*args, **kwargs)
    return wrapper

def no_log_zone_async(func: Callable[..., Any]) -> Callable[..., Any]:
    """Async variant of no_log_zone."""
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        with NoLogZone():
            return await func(*args, **kwargs)
    return wrapper

def no_log_zone_async_gen(func: Callable[..., Any]) -> Callable[..., Any]:
    """Async generator variant of no_log_zone."""
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        with NoLogZone():
            async for item in func(*args, **kwargs):
                yield item
    return wrapper
