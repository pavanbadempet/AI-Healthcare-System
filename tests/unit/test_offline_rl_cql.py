import pytest
from backend.ml.offline_rl_cql import ConservativeQLearningEngine, run_offline_rl_evaluation


def test_cql_offline_policy_evaluation():
    engine = ConservativeQLearningEngine()
    res = engine.evaluate_offline_policy()
    assert res.cql_safety_bound_passed is True
    assert res.value_improvement_pct == 18.0
    assert res.num_episodes_evaluated == 1000


def test_run_offline_rl_evaluation_helper():
    info = run_offline_rl_evaluation()
    assert info["safety_bound_passed"] is True
    assert info["policy_name"] == "Clinical_CQL_Conservative_Policy"
