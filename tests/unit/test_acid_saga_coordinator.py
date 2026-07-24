from backend.acid_saga_coordinator import DualEngineSagaCoordinator, SagaStep, run_sample_saga_transaction


def test_saga_coordinator_commit_success():
    coordinator = DualEngineSagaCoordinator()
    s1 = SagaStep("SQL_Step", lambda: None, lambda: None)
    s2 = SagaStep("Delta_Step", lambda: None, lambda: None)

    res = coordinator.execute_saga_transaction("TEST-SAGA-1", [s1, s2])
    assert res.status == "COMMITTED"
    assert res.acid_consistency_guaranteed is True
    assert len(res.completed_steps) == 2


def test_saga_coordinator_rollback_compensation():
    coordinator = DualEngineSagaCoordinator()

    def fail_step():
        raise RuntimeError("Simulated Delta Lake Write Failure")

    s1 = SagaStep("SQL_Step", lambda: None, lambda: None)
    s2 = SagaStep("Delta_Step_Fail", fail_step, lambda: None)

    res = coordinator.execute_saga_transaction("TEST-SAGA-FAIL", [s1, s2])
    assert res.status == "ROLLED_BACK"
    assert res.acid_consistency_guaranteed is True
    assert "SQL_Step" in res.compensated_steps


def test_run_sample_saga_transaction_helper():
    info = run_sample_saga_transaction()
    assert info["status"] == "COMMITTED"
    assert info["acid_guaranteed"] is True
