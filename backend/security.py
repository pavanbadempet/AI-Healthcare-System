"""
Security & Compliance Module
============================
Handles Audit Logging and Rate Limiting logic.
"""
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from . import audit, models

logger = logging.getLogger(__name__)

# --- Audit Logging ---

def log_audit_event(
    db: Session,
    action: str,
    target_user_id: int,
    admin_id: int = None,
    details: str = None
):
    """
    Log a security-critical event to the AuditLog table.

    Args:
        db: Database session
        action: Short string code (e.g. 'VIEW_PROFILE', 'DELETE_USER')
        target_user_id: ID of user affected
        admin_id: ID of admin performing action (optional)
        details: JSON string or text details
    """
    try:
        log_entry = models.AuditLog(
            admin_id=admin_id, # Can be None if system action
            target_user_id=target_user_id,
            action=action,
            details=audit.sanitize_audit_details(details),
            timestamp=datetime.now(timezone.utc)
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback() # Ensure ACID isolation by clearing failed transactions
        logger.error("Failed to write legacy audit log")


# --- Simple In-Memory / Redis Rate Limiter ---
# For scalable prod, we use Redis if REDIS_URL is provided and redis is installed.

def _load_rate_limit_requests_per_minute() -> int:
    raw_value = os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60")
    try:
        value = int(raw_value)
    except ValueError:
        raise RuntimeError("RATE_LIMIT_REQUESTS_PER_MINUTE must be an integer.")
    if value <= 0:
        raise RuntimeError("RATE_LIMIT_REQUESTS_PER_MINUTE must be positive.")
    return value


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.storage: Dict[str, list] = {}
        self.redis_client = None
        self.redis_available = False

        # Attempt to initialize Redis client if REDIS_URL is set
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis
                # Parse URL and create client
                self.redis_client = redis.from_url(redis_url, socket_timeout=1.0)
                # Test connectivity
                self.redis_client.ping()
                self.redis_available = True
                logger.info("Redis rate limiting initialized successfully.")
            except Exception as e:
                logger.warning(
                    "Redis connection for rate limiting failed: %s. Falling back to in-memory.",
                    e
                )

    def check(self, request: Request, identifier: str):
        """
        Check if request is allowed. Raises 429 if not.
        Uses a sliding window algorithm (implemented in Redis or in-memory).
        """
        now = time.time()

        if self.redis_available and self.redis_client:
            try:
                key = f"rate_limit:{identifier}"
                pipe = self.redis_client.pipeline()

                # Remove timestamps older than 60 seconds
                pipe.zremrangebyscore(key, 0, now - 60)
                # Count elements in sliding window
                pipe.zcard(key)
                # Add current timestamp
                pipe.zadd(key, {str(now): now})
                # Set TTL of 65s on key to clean up idle rate limit sets
                pipe.expire(key, 65)

                results = pipe.execute()
                current_count = results[1]

                if current_count >= self.requests_per_minute:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests. Please slow down."
                    )
                return
            except HTTPException:
                raise
            except Exception as e:
                logger.warning("Redis rate limit check failed: %s. Falling back to in-memory.", e)
                # Graceful degradation to in-memory

        # Cleanup old entries occasionally (simple garbage collection)
        if len(self.storage) > 1000:
            self._cleanup(now)

        history = self.storage.get(identifier, [])

        # Filter timestamps older than 60 seconds
        valid_history = [t for t in history if now - t < 60]

        if len(valid_history) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down."
            )

        valid_history.append(now)
        self.storage[identifier] = valid_history

    def _cleanup(self, now: float):
        keys_to_delete = []
        for key, history in self.storage.items():
            valid = [t for t in history if now - t < 60]
            if not valid:
                keys_to_delete.append(key)
            else:
                self.storage[key] = valid

        for k in keys_to_delete:
            del self.storage[k]

# Global instance
limiter = RateLimiter(requests_per_minute=_load_rate_limit_requests_per_minute())
