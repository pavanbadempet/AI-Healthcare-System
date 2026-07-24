"""
Unit tests for MG FcRn Receptor Antagonist Engine
"""

from backend.ml.mg_fcgrt_receptor_antagonist_engine import fcrn_engine


def test_evaluate_fcrn_cycle_response():
    res = fcrn_engine.evaluate_fcrn_antagonist_cycle(
        gmg_achr_or_musk_positive=True,
        baseline_mg_adl_score=10,
        current_mg_adl_score=4,
        weeks_since_last_cycle_start=3,
    )
    assert res["clinically_meaningful_response"] is True
    assert res["adl_improvement_points"] == 6
    assert res["reattendance_needed"] is False
    assert "Patient currently in clinical remission" in res["clinical_recommendation"]


def test_evaluate_fcrn_reattendance_needed():
    res = fcrn_engine.evaluate_fcrn_antagonist_cycle(
        gmg_achr_or_musk_positive=True,
        baseline_mg_adl_score=10,
        current_mg_adl_score=9,  # Rebound
        weeks_since_last_cycle_start=8,
    )
    assert res["reattendance_needed"] is True
    assert "INITIATE NEW FCRN ANTAGONIST CYCLE" in res["clinical_recommendation"]
