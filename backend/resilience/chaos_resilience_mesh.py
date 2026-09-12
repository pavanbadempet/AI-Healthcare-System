"""Autonomous Chaos Resilience Mesh and Self-Healing Circuit Breaker.

Provides in-process fault injection (programmable latency spikes, synthetic deadlocks,
connection drops) coupled with a 3-state sliding-window circuit breaker and automated
healing probes to ensure mission-critical clinical service survival during infrastructure chaos.
"""

from __future__ import annotations

import collections
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple


class ChaosFaultType(str, Enum):
    """Types of synthetic chaos faults injected into execution pipelines."""
    LATENCY_SPIKE = "LATENCY_SPIKE"
    TRANSIENT_ERROR = "TRANSIENT_ERROR"
    DEADLOCK = "DEADLOCK"
    DROP_PACKET = "DROP_PACKET"


class CircuitState(str, Enum):
    """Three-state operational circuit breaker phases."""
    CLOSED = "CLOSED"       # Normal flow, tracking failure rate
    OPEN = "OPEN"           # Tripped, failing fast to protect upstream
    HALF_OPEN = "HALF_OPEN" # Cooldown elapsed, admitting trial probes


class CircuitBreakerOpenError(Exception):
    """Raised when a request is rejected because the circuit breaker is OPEN."""
    def __init__(self, name: str, retry_after_sec: float) -> None:
        super().__init__(f"Circuit breaker '{name}' is OPEN. Retry after {retry_after_sec:.2f}s.")
        self.name = name
        self.retry_after_sec = retry_after_sec


class SyntheticChaosError(Exception):
    """Raised when an active chaos fault is triggered."""
    pass


@dataclass
class ChaosFaultRule:
    """Configuration for an active chaos fault injection rule."""
    fault_type: ChaosFaultType
    probability: float = 1.0
    delay_ms: float = 0.0
    error_message: str = "Synthetic fault injected by chaos mesh"
    target_endpoints: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class CircuitBreakerMetrics:
    """Telemetry metrics for a named circuit breaker."""
    name: str
    state: CircuitState
    failure_rate: float
    total_calls: int
    successful_calls: int
    failed_calls: int
    tripped_count: int
    last_state_change_utc: str


class SlidingWindowCircuitBreaker:
    """Sliding-window count-based circuit breaker with automated half-open recovery."""

    def __init__(
        self,
        name: str,
        failure_threshold_rate: float = 0.5,
        window_size: int = 10,
        cooldown_seconds: float = 2.0,
        half_open_trial_count: int = 3,
    ) -> None:
        self.name = name
        self.failure_threshold_rate = failure_threshold_rate
        self.window_size = window_size
        self.cooldown_seconds = cooldown_seconds
        self.half_open_trial_count = half_open_trial_count

        self._lock = threading.RLock()
        self._state = CircuitState.CLOSED
        self._history: Deque[bool] = collections.deque(maxlen=window_size)  # True = success, False = fail
        self._last_state_change_epoch: float = time.time()
        self._last_state_change_utc: str = datetime.now(timezone.utc).isoformat()
        self._half_open_successes: int = 0
        self._tripped_count: int = 0

        self._total_calls = 0
        self._success_calls = 0
        self._fail_calls = 0

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._evaluate_cooldown_transition()
            return self._state

    def _evaluate_cooldown_transition(self) -> None:
        """Transition from OPEN to HALF_OPEN if cooldown has expired."""
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_state_change_epoch
            if elapsed >= self.cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
                self._half_open_successes = 0
                self._last_state_change_epoch = time.time()
                self._last_state_change_utc = datetime.now(timezone.utc).isoformat()

    def execute(
        self,
        fn: Callable[..., Any],
        fallback_fn: Optional[Callable[..., Any]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Tuple[Any, bool]:
        """Execute callable through circuit breaker protection.

        Returns:
            Tuple of (result, used_fallback: bool)
        """
        with self._lock:
            self._evaluate_cooldown_transition()
            current_state = self._state

            if current_state == CircuitState.OPEN:
                retry_after = max(0.0, self.cooldown_seconds - (time.time() - self._last_state_change_epoch))
                if fallback_fn is not None:
                    return fallback_fn(*args, **kwargs), True
                raise CircuitBreakerOpenError(self.name, retry_after)

            self._total_calls += 1

        # Execute target callable outside the lock
        try:
            result = fn(*args, **kwargs)
            self._record_success()
            return result, False
        except Exception:
            self._record_failure()
            if fallback_fn is not None:
                return fallback_fn(*args, **kwargs), True
            raise

    def _record_success(self) -> None:
        with self._lock:
            self._success_calls += 1
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_successes += 1
                if self._half_open_successes >= self.half_open_trial_count:
                    # Circuit successfully recovered
                    self._state = CircuitState.CLOSED
                    self._history.clear()
                    self._last_state_change_epoch = time.time()
                    self._last_state_change_utc = datetime.now(timezone.utc).isoformat()
            elif self._state == CircuitState.CLOSED:
                self._history.append(True)

    def _record_failure(self) -> None:
        with self._lock:
            self._fail_calls += 1
            if self._state == CircuitState.HALF_OPEN:
                # Any failure during half-open immediately trips back to OPEN
                self._state = CircuitState.OPEN
                self._tripped_count += 1
                self._last_state_change_epoch = time.time()
                self._last_state_change_utc = datetime.now(timezone.utc).isoformat()
            elif self._state == CircuitState.CLOSED:
                self._history.append(False)
                if len(self._history) >= max(3, self.window_size // 2):
                    failures = sum(1 for x in self._history if not x)
                    fail_rate = failures / len(self._history)
                    if fail_rate >= self.failure_threshold_rate:
                        self._state = CircuitState.OPEN
                        self._tripped_count += 1
                        self._last_state_change_epoch = time.time()
                        self._last_state_change_utc = datetime.now(timezone.utc).isoformat()

    def get_metrics(self) -> CircuitBreakerMetrics:
        with self._lock:
            self._evaluate_cooldown_transition()
            if self._history:
                fail_rate = sum(1 for x in self._history if not x) / len(self._history)
            else:
                fail_rate = 0.0

            return CircuitBreakerMetrics(
                name=self.name,
                state=self._state,
                failure_rate=round(fail_rate, 3),
                total_calls=self._total_calls,
                successful_calls=self._success_calls,
                failed_calls=self._fail_calls,
                tripped_count=self._tripped_count,
                last_state_change_utc=self._last_state_change_utc,
            )

    def reset(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._history.clear()
            self._half_open_successes = 0
            self._last_state_change_epoch = time.time()
            self._last_state_change_utc = datetime.now(timezone.utc).isoformat()


class AutonomousChaosMesh:
    """In-process chaos simulator and circuit mesh manager."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._rules: Dict[str, ChaosFaultRule] = {}
        self._breakers: Dict[str, SlidingWindowCircuitBreaker] = {}

    def get_or_create_breaker(
        self,
        name: str,
        failure_threshold_rate: float = 0.5,
        window_size: int = 10,
        cooldown_seconds: float = 2.0,
    ) -> SlidingWindowCircuitBreaker:
        """Get or initialize a named sliding-window circuit breaker."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = SlidingWindowCircuitBreaker(
                    name=name,
                    failure_threshold_rate=failure_threshold_rate,
                    window_size=window_size,
                    cooldown_seconds=cooldown_seconds,
                )
            return self._breakers[name]

    def register_rule(self, rule_id: str, rule: ChaosFaultRule) -> None:
        """Register a chaos fault rule."""
        with self._lock:
            self._rules[rule_id] = rule

    def clear_rules(self) -> None:
        """Remove all active chaos rules."""
        with self._lock:
            self._rules.clear()

    def evaluate_chaos_interception(self, endpoint: str) -> Optional[str]:
        """Check if any active rule intercepts the specified endpoint and trigger it."""
        with self._lock:
            active_rules = [
                (rid, r) for rid, r in self._rules.items()
                if r.enabled and (not r.target_endpoints or endpoint in r.target_endpoints)
            ]

        for rule_id, rule in active_rules:
            if random.random() <= rule.probability:
                if rule.fault_type == ChaosFaultType.LATENCY_SPIKE:
                    time.sleep(rule.delay_ms / 1000.0)
                    return f"Injected {rule.delay_ms}ms latency spike ({rule_id})"
                elif rule.fault_type == ChaosFaultType.TRANSIENT_ERROR:
                    raise SyntheticChaosError(f"Transient error from rule {rule_id}: {rule.error_message}")
                elif rule.fault_type == ChaosFaultType.DEADLOCK:
                    raise SyntheticChaosError(f"Simulated deadlock condition ({rule_id})")
                elif rule.fault_type == ChaosFaultType.DROP_PACKET:
                    raise ConnectionResetError(f"Simulated network drop ({rule_id})")
        return None

    def get_all_metrics(self) -> Dict[str, Any]:
        """Aggregate telemetry from all registered circuit breakers and rules."""
        with self._lock:
            return {
                "active_chaos_rules": {
                    rid: {
                        "fault_type": r.fault_type.value,
                        "probability": r.probability,
                        "delay_ms": r.delay_ms,
                        "enabled": r.enabled,
                    }
                    for rid, r in self._rules.items()
                },
                "circuit_breakers": {
                    name: {
                        "state": b.state.value,
                        "failure_rate": b.get_metrics().failure_rate,
                        "tripped_count": b.get_metrics().tripped_count,
                        "total_calls": b.get_metrics().total_calls,
                    }
                    for name, b in self._breakers.items()
                },
            }
