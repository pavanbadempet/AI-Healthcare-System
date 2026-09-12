"""Adaptive Concurrency Limiter and Latency-Gradient Load Shedder.

Implements Little's Law (L = lambda * W) and TCP Vegas/CoDel gradient-based
dynamic concurrency control with priority-tiered load shedding to protect
mission-critical clinical actuations (ICU alarms, infusion rates) from latency spikes.
"""

from __future__ import annotations

import collections
import math
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, Tuple


class TrafficPriority(str, Enum):
    """Prioritized traffic classes for mission-critical clinical workloads."""
    CRITICAL_ACTUATION = "CRITICAL_ACTUATION"  # Life-critical (infusion pumps, code blue alarms)
    CLINICAL_QUERY = "CLINICAL_QUERY"          # Interactive clinician queries, EHR chart reads
    BACKGROUND_ANALYTICS = "BACKGROUND_ANALYTICS"  # Batch reporting, non-urgent data pipelines


@dataclass
class LimiterMetrics:
    """Snapshot of adaptive concurrency limiter operational state."""
    current_limit: float
    inflight_requests: int
    rtt_min_ms: float
    rtt_current_ms: float
    latency_gradient: float
    arrival_rate_rps: float
    estimated_littles_law_concurrency: float
    total_admitted: int
    total_shed: int
    shed_by_priority: Dict[str, int] = field(default_factory=dict)
    admitted_by_priority: Dict[str, int] = field(default_factory=dict)


class AdaptiveConcurrencyLimiter:
    """Dynamic concurrency limiter using latency gradient feedback and priority load-shedding."""

    def __init__(
        self,
        min_concurrency: float = 5.0,
        max_concurrency: float = 200.0,
        initial_concurrency: float = 20.0,
        smoothing_factor: float = 0.15,
        beta: float = 1.0,
        rtt_tolerance: float = 1.15,
        sample_window_size: int = 100,
    ) -> None:
        """Initialize the adaptive concurrency limiter.

        Args:
            min_concurrency: Hard lower bound on allowable concurrency.
            max_concurrency: Hard upper bound on allowable concurrency.
            initial_concurrency: Starting concurrency limit.
            smoothing_factor: Exponential moving average smoothing weight (alpha).
            beta: Additive increase constant during healthy gradient.
            rtt_tolerance: Multiplier above minimum RTT before congestion gradient dampens limit.
            sample_window_size: Size of rolling window for RTT observations.
        """
        self.min_concurrency = float(min_concurrency)
        self.max_concurrency = float(max_concurrency)
        self.current_limit = float(initial_concurrency)
        self.smoothing_factor = smoothing_factor
        self.beta = beta
        self.rtt_tolerance = rtt_tolerance

        self._lock = threading.RLock()
        self._inflight = 0
        self._rtt_min_ms: float = float("inf")
        self._rtt_current_ms: float = 10.0
        self._gradient: float = 1.0

        # Arrival rate tracking for Little's Law (L = lambda * W)
        self._arrival_timestamps: collections.deque[float] = collections.deque(maxlen=200)
        self._recent_rtts_ms: collections.deque[float] = collections.deque(maxlen=sample_window_size)

        self._admitted_counts: Dict[str, int] = {p.value: 0 for p in TrafficPriority}
        self._shed_counts: Dict[str, int] = {p.value: 0 for p in TrafficPriority}

    @property
    def inflight(self) -> int:
        """Current number of active inflight executions."""
        with self._lock:
            return self._inflight

    def evaluate_admission(self, priority: TrafficPriority) -> Tuple[bool, str, Dict[str, Any]]:
        """Evaluate if an incoming request can be admitted or must be shed.

        Args:
            priority: TrafficPriority tier of the request.

        Returns:
            Tuple of (admitted: bool, reason: str, metadata: dict)
        """
        with self._lock:
            now = time.time()
            self._arrival_timestamps.append(now)

            utilization = self._inflight / max(self.current_limit, 1.0)
            metadata = {
                "current_limit": round(self.current_limit, 2),
                "inflight": self._inflight,
                "utilization": round(utilization, 3),
                "gradient": round(self._gradient, 3),
                "priority": priority.value,
            }

            # Critical actuation has dedicated reserve headroom (up to 1.5x limit before emergency drop)
            if priority == TrafficPriority.CRITICAL_ACTUATION:
                if self._inflight < self.current_limit * 1.5:
                    self._inflight += 1
                    self._admitted_counts[priority.value] += 1
                    return True, "ADMITTED_CRITICAL_RESERVE", metadata
                self._shed_counts[priority.value] += 1
                return False, "SHED_CRITICAL_CAPACITY_EXHAUSTED", metadata

            # Clinical queries admitted if utilization < 90%
            if priority == TrafficPriority.CLINICAL_QUERY:
                if utilization < 0.90:
                    self._inflight += 1
                    self._admitted_counts[priority.value] += 1
                    return True, "ADMITTED_CLINICAL", metadata
                self._shed_counts[priority.value] += 1
                return False, "SHED_CLINICAL_CONGESTION", metadata

            # Background analytics admitted only if system is under 60% capacity
            if priority == TrafficPriority.BACKGROUND_ANALYTICS:
                if utilization < 0.60:
                    self._inflight += 1
                    self._admitted_counts[priority.value] += 1
                    return True, "ADMITTED_BACKGROUND", metadata
                self._shed_counts[priority.value] += 1
                return False, "SHED_BACKGROUND_CONGESTION", metadata

            # Fallback
            self._shed_counts[priority.value] += 1
            return False, "SHED_UNKNOWN_PRIORITY", metadata

    def record_completion(self, latency_ms: float) -> None:
        """Record the latency of a completed request and update adaptive limit.

        Args:
            latency_ms: Execution duration in milliseconds.
        """
        with self._lock:
            self._inflight = max(0, self._inflight - 1)
            valid_latency = max(0.1, float(latency_ms))
            self._recent_rtts_ms.append(valid_latency)

            # Update baseline minimum RTT
            if valid_latency < self._rtt_min_ms:
                self._rtt_min_ms = valid_latency

            # Exponential Moving Average of current RTT
            self._rtt_current_ms = (
                (1.0 - self.smoothing_factor) * self._rtt_current_ms
                + self.smoothing_factor * valid_latency
            )

            # Latency gradient: RTT_min * tolerance / max(RTT_current, RTT_min)
            effective_min = self._rtt_min_ms * self.rtt_tolerance
            raw_gradient = effective_min / max(self._rtt_current_ms, self._rtt_min_ms)
            # Clamp gradient to avoid wild divergence
            self._gradient = max(0.2, min(raw_gradient, 2.0))

            # Dynamic limit update: limit_{t+1} = limit_t * gradient + beta
            if self._gradient >= 1.0:
                # Sub-congested: additive increase
                new_limit = self.current_limit + self.beta
            else:
                # Congested: multiplicative backoff weighted by gradient
                new_limit = self.current_limit * self._gradient

            self.current_limit = max(
                self.min_concurrency, min(new_limit, self.max_concurrency)
            )

    @contextmanager
    def guard(self, priority: TrafficPriority) -> Iterator[Tuple[bool, str, Dict[str, Any]]]:
        """Context manager to guard a block with admission check and timing.

        Yields:
            Tuple of (admitted: bool, reason: str, metadata: dict)
        """
        admitted, reason, meta = self.evaluate_admission(priority)
        if not admitted:
            yield False, reason, meta
            return

        start_time = time.perf_counter()
        try:
            yield True, reason, meta
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            self.record_completion(duration_ms)

    def get_metrics(self) -> LimiterMetrics:
        """Compute operational metrics including Little's Law concurrency estimate."""
        with self._lock:
            # Calculate arrival rate lambda (requests / sec) over recent arrivals
            if len(self._arrival_timestamps) >= 2:
                time_span = max(0.001, self._arrival_timestamps[-1] - self._arrival_timestamps[0])
                arrival_rate = len(self._arrival_timestamps) / time_span
            else:
                arrival_rate = 0.0

            # Little's Law: L = lambda * W
            mean_latency_sec = (self._rtt_current_ms / 1000.0) if self._rtt_current_ms > 0 else 0.001
            littles_law_concurrency = arrival_rate * mean_latency_sec

            total_admitted = sum(self._admitted_counts.values())
            total_shed = sum(self._shed_counts.values())

            return LimiterMetrics(
                current_limit=round(self.current_limit, 2),
                inflight_requests=self._inflight,
                rtt_min_ms=round(self._rtt_min_ms if math.isfinite(self._rtt_min_ms) else 0.0, 2),
                rtt_current_ms=round(self._rtt_current_ms, 2),
                latency_gradient=round(self._gradient, 3),
                arrival_rate_rps=round(arrival_rate, 2),
                estimated_littles_law_concurrency=round(littles_law_concurrency, 2),
                total_admitted=total_admitted,
                total_shed=total_shed,
                shed_by_priority=dict(self._shed_counts),
                admitted_by_priority=dict(self._admitted_counts),
            )
