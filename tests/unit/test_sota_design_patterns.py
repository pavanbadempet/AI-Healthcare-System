"""
Unit tests for SOTA Software Design Patterns (Circuit Breaker, Outbox, Saga Orchestrator).
"""

import pytest

from backend.sota_design_patterns import CircuitBreaker, CircuitState, SagaOrchestrator, SagaStep, outbox_engine


def test_circuit_breaker_resilience():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=1.0)

    def failing_func():
        raise ValueError("Service unavailable")

    with pytest.raises(ValueError):
        cb.execute(failing_func)
    assert cb.state == CircuitState.CLOSED

    with pytest.raises(ValueError):
        cb.execute(failing_func)
    assert cb.state == CircuitState.OPEN

    with pytest.raises(RuntimeError):
        cb.execute(failing_func)

def test_transactional_outbox_pattern():
    msg = outbox_engine.stage_event("PATIENT_ADMISSION", "P-99", {"ward": "Cardiology"})
    assert msg.processed is False
    count = outbox_engine.dispatch_pending_events()
    assert count >= 1
    assert msg.processed is True

def test_saga_orchestrator_successful_flow():
    state = {"step1": False, "step2": False}
    saga = SagaOrchestrator()
    saga.add_step(SagaStep(lambda: state.update({"step1": True}) or True, lambda: state.update({"step1": False}), "Step1"))
    saga.add_step(SagaStep(lambda: state.update({"step2": True}) or True, lambda: state.update({"step2": False}), "Step2"))

    res = saga.execute_saga()
    assert res is True
    assert state["step1"] is True
    assert state["step2"] is True

def test_saga_orchestrator_compensation_rollback():
    rollback_history = []
    saga = SagaOrchestrator()
    saga.add_step(SagaStep(lambda: True, lambda: rollback_history.append("RollbackStep1"), "Step1"))
    saga.add_step(SagaStep(lambda: False, lambda: rollback_history.append("RollbackStep2"), "Step2 Fails"))

    res = saga.execute_saga()
    assert res is False
    assert "RollbackStep1" in rollback_history
