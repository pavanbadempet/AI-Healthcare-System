"""Cryptographic Idempotency and Deterministic Exactly-Once Execution Engine.

Guarantees exactly-once execution semantics for life-critical clinical operations
(medication administration, ICU actuator commands, billing transactions) over flaky
hospital networks. Detects payload tampering and provides deterministic response replay.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple


class IdempotencyState(str, Enum):
    """Lifecycle states of an idempotent execution."""
    PENDING = "PENDING"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"


class IdempotencyConflictError(Exception):
    """Raised when an idempotency key is reused with a mutated payload or method."""
    def __init__(self, key: str, original_fingerprint: str, new_fingerprint: str) -> None:
        super().__init__(
            f"Idempotency conflict for key '{key}': incoming fingerprint '{new_fingerprint[:12]}...' "
            f"does not match registered fingerprint '{original_fingerprint[:12]}...'."
        )
        self.key = key
        self.original_fingerprint = original_fingerprint
        self.new_fingerprint = new_fingerprint


class IdempotencyExecutionInProgressError(Exception):
    """Raised when a concurrent request with identical key is already in progress."""
    def __init__(self, key: str) -> None:
        super().__init__(f"Operation with idempotency key '{key}' is currently executing.")
        self.key = key


@dataclass
class IdempotencyRecord:
    """Persistent representation of an idempotent request execution."""
    key: str
    fingerprint: str
    method: str
    path: str
    state: IdempotencyState
    created_at_utc: str
    updated_at_utc: str
    status_code: Optional[int] = None
    response_body: Optional[Any] = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    replay_count: int = 0
    expires_at_epoch: float = 0.0


def canonical_json_hash(payload: Any) -> str:
    """Generate deterministic SHA-256 hash of arbitrary JSON-compatible payload."""
    if payload is None:
        serialized = "null"
    elif isinstance(payload, (dict, list, int, float, str, bool)):
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    else:
        serialized = str(payload)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_request_fingerprint(key: str, method: str, path: str, payload: Any) -> str:
    """Compute cryptographic fingerprint over key, HTTP method, target path, and payload.

    Formula: SHA-256(key + ':' + method + ':' + path + ':' + SHA-256(payload))
    """
    payload_digest = canonical_json_hash(payload)
    seed = f"{key}:{method.upper().strip()}:{path.strip()}:{payload_digest}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


class CryptographicIdempotencyEngine:
    """Thread-safe cryptographic idempotency manager with replay and conflict detection."""

    def __init__(self, default_ttl_seconds: int = 86400) -> None:
        """Initialize idempotency engine.

        Args:
            default_ttl_seconds: Record retention window in seconds (default: 24h).
        """
        self.default_ttl_seconds = default_ttl_seconds
        self._lock = threading.RLock()
        self._records: Dict[str, IdempotencyRecord] = {}
        self._events: Dict[str, threading.Event] = {}

    def execute_idempotent(
        self,
        key: str,
        method: str,
        path: str,
        payload: Any,
        execution_handler: Callable[[], Tuple[int, Any, Dict[str, str]]],
        wait_timeout_seconds: float = 5.0,
    ) -> Tuple[int, Any, Dict[str, str], bool]:
        """Execute action idempotently or replay prior deterministic response.

        Args:
            key: Client-provided idempotency key.
            method: HTTP method (e.g., 'POST').
            path: Target URI path.
            payload: Request payload object or dict.
            execution_handler: Callable executing the business logic if not already committed.
            wait_timeout_seconds: Timeout to wait if another thread is currently executing.

        Returns:
            Tuple of (status_code, response_body, response_headers, is_replay)
        """
        if not key or not key.strip():
            # Non-idempotent passthrough
            status_code, body, headers = execution_handler()
            return status_code, body, headers, False

        fingerprint = compute_request_fingerprint(key, method, path, payload)
        now_epoch = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()

        event_to_wait: Optional[threading.Event] = None

        with self._lock:
            # Clean up expired record if present
            if key in self._records and self._records[key].expires_at_epoch < now_epoch:
                del self._records[key]
                if key in self._events:
                    del self._events[key]

            existing = self._records.get(key)
            if existing is not None:
                # Tamper detection: verify fingerprint
                if existing.fingerprint != fingerprint:
                    raise IdempotencyConflictError(
                        key=key,
                        original_fingerprint=existing.fingerprint,
                        new_fingerprint=fingerprint,
                    )

                # Committed: Deterministic response replay
                if existing.state == IdempotencyState.COMMITTED:
                    existing.replay_count += 1
                    existing.updated_at_utc = now_iso
                    replay_headers = dict(existing.response_headers)
                    replay_headers["X-Idempotent-Replay"] = "true"
                    replay_headers["X-Idempotency-Key"] = key
                    return (
                        existing.status_code or 200,
                        existing.response_body,
                        replay_headers,
                        True,
                    )

                # Pending: Concurrent in-flight request detected
                if existing.state == IdempotencyState.PENDING:
                    event_to_wait = self._events.get(key)
            else:
                # Claim key with PENDING state
                record = IdempotencyRecord(
                    key=key,
                    fingerprint=fingerprint,
                    method=method.upper(),
                    path=path,
                    state=IdempotencyState.PENDING,
                    created_at_utc=now_iso,
                    updated_at_utc=now_iso,
                    expires_at_epoch=now_epoch + self.default_ttl_seconds,
                )
                self._records[key] = record
                event = threading.Event()
                self._events[key] = event

        # Wait for concurrent pending execution if applicable
        if event_to_wait is not None:
            signaled = event_to_wait.wait(timeout=wait_timeout_seconds)
            if not signaled:
                raise IdempotencyExecutionInProgressError(key=key)

            # Re-read committed state
            with self._lock:
                record = self._records.get(key)
                if record and record.state == IdempotencyState.COMMITTED:
                    record.replay_count += 1
                    record.updated_at_utc = datetime.now(timezone.utc).isoformat()
                    replay_headers = dict(record.response_headers)
                    replay_headers["X-Idempotent-Replay"] = "true"
                    replay_headers["X-Idempotency-Key"] = key
                    return (
                        record.status_code or 200,
                        record.response_body,
                        replay_headers,
                        True,
                    )
                raise IdempotencyExecutionInProgressError(key=key)

        # Primary execution thread
        try:
            status_code, body, headers = execution_handler()
            with self._lock:
                rec = self._records[key]
                rec.state = IdempotencyState.COMMITTED
                rec.status_code = status_code
                rec.response_body = body
                rec.response_headers = headers or {}
                rec.updated_at_utc = datetime.now(timezone.utc).isoformat()

                out_headers = dict(headers or {})
                out_headers["X-Idempotent-Replay"] = "false"
                out_headers["X-Idempotency-Key"] = key

                if key in self._events:
                    self._events[key].set()

            return status_code, body, out_headers, False

        except Exception as exc:
            with self._lock:
                if key in self._records:
                    rec = self._records[key]
                    rec.state = IdempotencyState.FAILED
                    rec.error_message = str(exc)
                    rec.updated_at_utc = datetime.now(timezone.utc).isoformat()
                if key in self._events:
                    self._events[key].set()
            raise

    def get_record(self, key: str) -> Optional[IdempotencyRecord]:
        """Retrieve stored record for an idempotency key."""
        with self._lock:
            return self._records.get(key)

    def count(self) -> int:
        """Return total active idempotency records."""
        with self._lock:
            return len(self._records)
