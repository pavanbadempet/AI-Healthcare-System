"""
Security & Compliance Module
============================
Handles Audit Logging and Rate Limiting logic.
"""
from sqlalchemy.orm import Session
from . import models
from fastapi import Request, HTTPException
from datetime import datetime, timezone
import time
import logging
from typing import Dict, Tuple

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
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"FAILED TO AUDIT LOG: {e}")
        # Don't crash the app if logging fails, just log error
        pass


# --- Simple In-Memory Rate Limiter ---
# For scalable prod, use Redis. For MVP/Free Tier, this suffices.

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.storage: Dict[str, list] = {}
        
    def check(self, request: Request, identifier: str):
        """
        Check if request is allowed. Raises 429 if not.
        Uses a sliding window algorithm.
        """
        now = time.time()
        
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
limiter = RateLimiter(requests_per_minute=60)
