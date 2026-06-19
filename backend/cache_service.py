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
    _instance: Optional['SystemCache'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'SystemCache':
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
                    self.redis_client = redis.Redis.from_url(
                        url,
                        socket_timeout=2.0,
                        decode_responses=False
                    )
                else:
                    self.redis_client = redis.Redis(
                        host=REDIS_HOST,
                        port=REDIS_PORT,
                        password=REDIS_PASSWORD,
                        db=REDIS_DB,
                        socket_timeout=2.0,
                        decode_responses=False # Keep binary/pickle serialization flexible
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
            logger.info("No Redis configuration found (neither REDIS_URL nor REDIS_HOST). Initialized in-memory TTL cache.")

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
                    self.redis_client.setex(key, ttl, serialized)
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

# Global cache helper
cache = SystemCache()
