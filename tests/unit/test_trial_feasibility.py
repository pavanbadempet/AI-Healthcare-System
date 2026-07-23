"""
Unit tests for Trial Feasibility Simulator
"""

import pytest
from backend.ml.trial_feasibility_simulator import ClinicalTrialFeasibilitySimulator, trial_feasibility_simulator


def test_simulate_trial_feasibility_success():
    res = trial_feasibility_simulator.simulate_trial_feasibility(
        target_sample_size=100,
        monthly_recruitment_rate=15,
        expected_dropout_pct=10.0,
        trial_duration_months=12,
    )
    assert res["is_feasible"] is True
    assert res["feasibility_status"] == "FEASIBLE"
    assert res["projected_retained"] >= 100


def test_simulate_trial_feasibility_shortfall():
    res = trial_feasibility_simulator.simulate_trial_feasibility(
        target_sample_size=500,
        monthly_recruitment_rate=10,
        expected_dropout_pct=20.0,
        trial_duration_months=12,
    )
    assert res["is_feasible"] is False
    assert res["feasibility_status"] == "UNDERPOWERED_SHORTFALL"
