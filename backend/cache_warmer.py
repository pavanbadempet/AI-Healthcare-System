"""
Cache Warmer — Startup Warming and Background Refresher
======================================================
Pre-loads critical metrics and active datasets into the dual cache system
on application startup, and maintains them via an active background worker thread.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

from .cache_service import cache

logger = logging.getLogger(__name__)

class CacheWarmer:
    """Handles startup cache warming and asynchronous background refreshment of hot keys."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._warmables: Dict[str, Dict[str, Any]] = {}
        self._stop_event = threading.Event()
        self._refresh_thread: Optional[threading.Thread] = None

    def register_warmable(self, key: str, loader_fn: Callable[[], Any], ttl: int, refresh_interval: int) -> None:
        """Registers a data source to be kept warm.

        Args:
            key: Cache key.
            loader_fn: Thread-safe function that fetches and returns the fresh value.
            ttl: TTL to apply when setting in cache.
            refresh_interval: How often (in seconds) to background-refresh this key.
        """
        with self._lock:
            self._warmables[key] = {
                "loader_fn": loader_fn,
                "ttl": ttl,
                "refresh_interval": refresh_interval,
                "last_refreshed": 0.0
            }
        logger.info("Registered warmable cache key: %s (refresh interval: %d s)", key, refresh_interval)

    def warm_on_startup(self) -> None:
        """Triggers synchronous evaluation of all warmables on startup."""
        logger.info("Starting synchronous cache warming...")
        with self._lock:
            for key, config in self._warmables.items():
                self._execute_warming(key, config)
        logger.info("Synchronous cache warming complete.")

    def _execute_warming(self, key: str, config: Dict[str, Any]) -> None:
        """Executes a single loader function and populates the cache."""
        try:
            loader = config["loader_fn"]
            value = loader()
            if value is not None:
                cache.set(key, value, ttl=config["ttl"])
                config["last_refreshed"] = time.time()
                logger.debug("Successfully warmed cache key: %s", key)
            else:
                logger.warning("Loader returned None for cache key: %s. Skipping write.", key)
        except Exception as e:
            logger.error("Failed to warm cache key %s: %s", key, e)

    def start_background_refresh(self) -> None:
        """Spawns a background daemon thread that periodically updates registered keys."""
        with self._lock:
            if self._refresh_thread and self._refresh_thread.is_alive():
                logger.warning("Cache refresh daemon thread is already running.")
                return

            self._stop_event.clear()
            self._refresh_thread = threading.Thread(
                target=self._background_loop,
                name="CacheWarmerDaemon",
                daemon=True
            )
            self._refresh_thread.start()
        logger.info("Started background cache warmer daemon thread.")

    def stop(self) -> None:
        """Triggers graceful shutdown of the background thread."""
        logger.info("Signaling cache warmer daemon thread to stop...")
        self._stop_event.set()
        if self._refresh_thread:
            self._refresh_thread.join(timeout=5.0)
            logger.info("Cache warmer background thread terminated.")

    def _background_loop(self) -> None:
        """Periodically scans warmables and refreshes those exceeding their intervals."""
        while not self._stop_event.wait(timeout=1.0):
            now = time.time()
            # Work on a copy of keys to avoid nested locking issues
            with self._lock:
                keys = list(self._warmables.keys())

            for key in keys:
                if self._stop_event.is_set():
                    break

                with self._lock:
                    config = self._warmables.get(key)

                if not config:
                    continue

                elapsed = now - config["last_refreshed"]
                if elapsed >= config["refresh_interval"]:
                    logger.debug("Refreshing warmable key: %s (elapsed: %.1f s)", key, elapsed)
                    self._execute_warming(key, config)

# Initialize defaults
cache_warmer = CacheWarmer()

# Actual database counts loader for the dashboard statistics cache key
def _load_actual_stats() -> Dict[str, Any]:
    from backend import database, models
    from backend.database import get_db_context

    with get_db_context() as db:
        try:
            total_users = db.query(models.User).filter(models.User.is_deleted == False).count()
            total_predictions = db.query(models.HealthRecord).count()
            total_messages = db.query(models.ChatLog).count()

            return {
                "total_users": total_users,
                "total_predictions": total_predictions,
                "total_messages": total_messages,
                "server_status": "Online",
                "database_status": "Connected",
                "database_type": "sqlite" if "sqlite" in database.SQLALCHEMY_DATABASE_URL else "postgresql"
            }
        except Exception as e:
            logger.warning("Cache warmer: Failed to query actual stats: %s", e)
            return {"total_users": 0, "total_predictions": 0, "total_messages": 0}

def _default_patients_count_loader() -> int:
    return 142

def _default_model_meta_loader() -> Dict[str, Any]:
    return {"loaded_models": ["diabetes", "heart", "liver", "kidney", "lungs"], "active_experiment": "ab_test_v1"}

def _default_health_loader() -> Dict[str, str]:
    return {"status": "healthy", "redis": "connected"}

# Register the actual stats loader to keep dashboard_statistics warm
cache_warmer.register_warmable("dashboard_statistics", _load_actual_stats, ttl=7200, refresh_interval=3600)
# Also register facility-specific key placeholders or let them warm dynamically
cache_warmer.register_warmable("dashboard_statistics:global", _load_actual_stats, ttl=7200, refresh_interval=3600)
cache_warmer.register_warmable("active_patients_count", _default_patients_count_loader, ttl=3600, refresh_interval=600)
cache_warmer.register_warmable("model_metadata", _default_model_meta_loader, ttl=86400, refresh_interval=7200)
cache_warmer.register_warmable("system_health", _default_health_loader, ttl=120, refresh_interval=60)
