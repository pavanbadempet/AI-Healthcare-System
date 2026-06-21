"""
System Caching Service — Thread-safe In-Memory & Redis Fallback Cache
=====================================================================
Provides low-latency caching for heavy SQL reads, API results, and LLM/embedding inference.
Falls back silently to an in-memory TTL dictionary if Redis is not configured or unavailable.
"""

import logging
import os
import threading
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Redis configuration from environment variables
REDIS_URL = os.environ.get("REDIS_URL", None)
REDIS_HOST = os.environ.get("REDIS_HOST", None)
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))


class SystemCache:
    """Thread-safe dual-backend cache (Redis with silent In-Memory fallback)."""

    _instance: Optional["SystemCache"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SystemCache":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_cache()
            return cls._instance

    def _init_cache(self):
        self._in_memory_store = {}
        self._store_lock = threading.Lock()
        self.redis_client = None

        if REDIS_URL or REDIS_HOST:
            try:
                import redis

                if REDIS_URL:
                    # Strip quotes if present (common in .env files)
                    url = REDIS_URL.strip('"').strip("'")
                    self.redis_client = redis.Redis.from_url(url, socket_timeout=2.0, decode_responses=False)
                else:
                    self.redis_client = redis.Redis(
                        host=REDIS_HOST,
                        port=REDIS_PORT,
                        password=REDIS_PASSWORD,
                        db=REDIS_DB,
                        socket_timeout=2.0,
                        decode_responses=False,  # Keep binary/pickle serialization flexible
                    )
                # Test connection
                self.redis_client.ping()
                if REDIS_URL:
                    logger.info("Connected to Redis cache server using REDIS_URL")
                else:
                    logger.info("Connected to Redis cache server at %s:%d", REDIS_HOST, REDIS_PORT)
            except Exception as e:
                logger.warning("Redis configured but failed to connect (falling back to in-memory): %s", e)
                self.redis_client = None
        else:
            logger.info(
                "No Redis configuration found (neither REDIS_URL nor REDIS_HOST). Initialized in-memory TTL cache."
            )

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache. Returns None on cache miss or expiration."""
        if self.redis_client:
            try:
                import pickle

                val = self.redis_client.get(key)
                if val is not None:
                    return pickle.loads(val)
            except Exception as e:
                logger.warning("Redis get failed: %s", e)

        # In-memory fallback
        with self._store_lock:
            entry = self._in_memory_store.get(key)
            if entry:
                expiry, val = entry
                if expiry is None or expiry > time.time():
                    return val
                else:
                    # Clean up expired key
                    self._in_memory_store.pop(key, None)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in the cache with an optional TTL (in seconds)."""
        if self.redis_client:
            try:
                import pickle

                serialized = pickle.dumps(value)
                if ttl:
                    self.redis_client.set(key, serialized, ex=ttl)
                else:
                    self.redis_client.set(key, serialized)
                return
            except Exception as e:
                logger.warning("Redis set failed: %s", e)

        # In-memory fallback
        with self._store_lock:
            expiry = (time.time() + ttl) if ttl else None
            self._in_memory_store[key] = (expiry, value)

    def delete(self, key: str) -> bool:
        """Remove a key from the cache. Returns True if key existed."""
        existed = False
        if self.redis_client:
            try:
                existed = bool(self.redis_client.delete(key))
            except Exception as e:
                logger.warning("Redis delete failed: %s", e)

        with self._store_lock:
            if key in self._in_memory_store:
                self._in_memory_store.pop(key)
                existed = True
        return existed

    def clear(self) -> None:
        """Clear all cached keys."""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.warning("Redis flushdb failed: %s", e)

        with self._store_lock:
            self._in_memory_store.clear()

    # ── Cache Metrics ──────────────────────────────────────────────────
    _hits: int = 0
    _misses: int = 0

    def record_hit(self) -> None:
        """Increment cache hit counter."""
        self._hits += 1

    def record_miss(self) -> None:
        """Increment cache miss counter."""
        self._misses += 1

    @property
    def hit_rate(self) -> float:
        """Return cache hit rate as a float between 0.0 and 1.0."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> dict:
        """Return cache statistics."""
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total": total,
            "hit_rate": self.hit_rate,
            "backend": "redis" if self.redis_client else "in_memory",
            "in_memory_keys": len(self._in_memory_store),
        }

    def get_with_metrics(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache, recording hit/miss metrics."""
        value = self.get(key)
        if value is not None:
            self.record_hit()
        else:
            self.record_miss()
        return value

    # ── Serialization helpers (msgpack preferred, pickle fallback) ────
    @staticmethod
    def _serialize(value: Any) -> bytes:
        """Serialize a value using msgpack if available, otherwise pickle."""
        try:
            import msgpack

            return msgpack.packb(value, use_bin_type=True, default=str)
        except (ImportError, TypeError):
            import pickle

            return pickle.dumps(value)

    @staticmethod
    def _deserialize(data: bytes) -> Any:
        """Deserialize bytes using msgpack if available, otherwise pickle."""
        try:
            import msgpack

            return msgpack.unpackb(data, raw=False)
        except (ImportError, Exception):
            import pickle

            return pickle.loads(data)

    def safe_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value using secure serialization (msgpack preferred)."""
        if self.redis_client:
            try:
                serialized = self._serialize(value)
                if ttl:
                    self.redis_client.set(key, serialized, ex=ttl)
                else:
                    self.redis_client.set(key, serialized)
                return
            except Exception as e:
                logger.warning("Redis safe_set failed: %s", e)
        # In-memory fallback
        with self._store_lock:
            expiry = (time.time() + ttl) if ttl else None
            self._in_memory_store[key] = (expiry, value)

    def safe_get(self, key: str) -> Optional[Any]:
        """Retrieve a value using secure deserialization (msgpack preferred)."""
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val is not None:
                    self.record_hit()
                    return self._deserialize(val)
            except Exception as e:
                logger.warning("Redis safe_get failed: %s", e)
        # In-memory fallback
        with self._store_lock:
            entry = self._in_memory_store.get(key)
            if entry:
                expiry, val = entry
                if expiry is None or expiry > time.time():
                    self.record_hit()
                    return val
                else:
                    self._in_memory_store.pop(key, None)
        self.record_miss()
        return None


# ── API Response Caching Decorator ─────────────────────────────────────
import functools
import hashlib


def cached_response(ttl: int = 300, key_prefix: str = "api"):
    """
    FastAPI endpoint caching decorator.

    Caches the return value of a route handler based on its arguments.
    Automatically invalidated after ``ttl`` seconds.

    Usage::

        @router.get("/dashboard/stats")
        @cached_response(ttl=60, key_prefix="dashboard")
        async def get_dashboard_stats(db: Session = Depends(get_db)):
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Build a cache key from the function name and hashable args
            key_parts = [key_prefix, func.__module__, func.__qualname__]
            # Include only serializable kwargs (skip db sessions, requests, etc.)
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool, type(None))):
                    key_parts.append(f"{k}={v}")
            raw_key = ":".join(key_parts)
            cache_key = f"resp:{hashlib.sha256(raw_key.encode()).hexdigest()[:16]}"

            # Try cache first
            cached = cache.get_with_metrics(cache_key)
            if cached is not None:
                return cached

            # Call the actual function
            result = await func(*args, **kwargs)

            # Cache the result
            try:
                cache.set(cache_key, result, ttl=ttl)
            except Exception as e:
                logger.warning("Failed to cache response for %s: %s", func.__qualname__, e)

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            key_parts = [key_prefix, func.__module__, func.__qualname__]
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool, type(None))):
                    key_parts.append(f"{k}={v}")
            raw_key = ":".join(key_parts)
            cache_key = f"resp:{hashlib.sha256(raw_key.encode()).hexdigest()[:16]}"

            cached = cache.get_with_metrics(cache_key)
            if cached is not None:
                return cached

            result = func(*args, **kwargs)
            try:
                cache.set(cache_key, result, ttl=ttl)
            except Exception as e:
                logger.warning("Failed to cache response for %s: %s", func.__qualname__, e)
            return result

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def invalidate_cache_prefix(prefix: str) -> int:
    """
    Invalidate all cache keys matching a prefix.
    Returns count of keys invalidated.
    """
    count = 0
    with cache._store_lock:
        keys_to_remove = [k for k in cache._in_memory_store if k.startswith(f"resp:{prefix}")]
        for key in keys_to_remove:
            cache._in_memory_store.pop(key, None)
            count += 1
    if cache.redis_client:
        try:
            cursor = 0
            while True:
                cursor, keys = cache.redis_client.scan(cursor, match=f"resp:{prefix}*", count=100)
                for key in keys:
                    cache.redis_client.delete(key)
                    count += 1
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning("Redis invalidation scan failed: %s", e)
    return count


# Global cache helper
cache = SystemCache()
