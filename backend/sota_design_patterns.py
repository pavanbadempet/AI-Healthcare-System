"""
Backward-compatibility bridge for backend.circuit_breaker
"""
from backend.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    OutboxMessage,
    SagaOrchestrator,
    SagaStep,
    TransactionalOutboxEngine,
    outbox_engine,
)
