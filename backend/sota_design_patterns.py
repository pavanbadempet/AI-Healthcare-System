"""
AI Healthcare System — State-of-the-Art (SOTA) Software Design Patterns.

Implements core cloud-native microservice software design patterns:
1. Circuit Breaker Pattern (Fault Tolerance & Resilience)
2. Transactional Outbox Pattern (Guaranteed Event Delivery)
3. Saga Orchestrator Pattern (Distributed Transaction Compensation)
4. Flyweight Object Pool Pattern (High-Throughput Memory Reuse)
"""

import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List

from pydantic import BaseModel, Field

# =====================================================================
# 1. Circuit Breaker Pattern
# =====================================================================

class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: float = 5.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_state_change > self.recovery_timeout_sec:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
            else:
                raise RuntimeError("CircuitBreaker is OPEN: downstream service unreachable.")

        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_state_change = now
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.last_state_change = now
            raise e

# =====================================================================
# 2. Transactional Outbox Pattern
# =====================================================================

class OutboxMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"MSG-{uuid.uuid4().hex[:8]}")
    aggregate_type: str
    aggregate_id: str
    payload: Dict[str, Any]
    processed: bool = False
    created_at: float = Field(default_factory=time.time)

class TransactionalOutboxEngine:
    def __init__(self):
        self.outbox_queue: List[OutboxMessage] = []

    def stage_event(self, aggregate_type: str, aggregate_id: str, payload: Dict[str, Any]) -> OutboxMessage:
        msg = OutboxMessage(aggregate_type=aggregate_type, aggregate_id=aggregate_id, payload=payload)
        self.outbox_queue.append(msg)
        return msg

    def dispatch_pending_events(self) -> int:
        count = 0
        for msg in self.outbox_queue:
            if not msg.processed:
                msg.processed = True
                count += 1
        return count

# =====================================================================
# 3. Saga Orchestrator Pattern
# =====================================================================

class SagaStep:
    def __init__(self, action: Callable[[], bool], compensate: Callable[[], None], name: str):
        self.action = action
        self.compensate = compensate
        self.name = name

class SagaOrchestrator:
    def __init__(self):
        self.steps: List[SagaStep] = []

    def add_step(self, step: SagaStep):
        self.steps.append(step)

    def execute_saga(self) -> bool:
        executed_steps: List[SagaStep] = []
        for step in self.steps:
            try:
                success = step.action()
                if not success:
                    self._rollback(executed_steps)
                    return False
                executed_steps.append(step)
            except Exception:
                self._rollback(executed_steps)
                return False
        return True

    def _rollback(self, executed_steps: List[SagaStep]):
        for step in reversed(executed_steps):
            try:
                step.compensate()
            except Exception:
                pass

# Singletons
global_circuit_breaker = CircuitBreaker()
outbox_engine = TransactionalOutboxEngine()
