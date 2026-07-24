"""
Unit tests for HAPE/HACE Risk Evaluator
"""

from backend.ml.hape_hace_risk_evaluator import hape_hace_evaluator


def test_evaluate_altitude_illness_hace():
    res = hape_hace_evaluator.evaluate_altitude_illness(
        headache_severity=3,
        gastrointestinal_nausea=2,
        fatigue_weakness=3,
        dizziness_lightheadedness=2,
        dyspnea_at_rest=True,
        ataxia_staggering_gait=True,
    )
    assert res["emergency_level"] == "STAT_ALTITUDE_EMERGENCY"
    assert res["hace_suspected"] is True
    assert res["immediate_descent_required"] is True
    assert "Dexamethasone" in res["clinical_recommendation"]


def test_evaluate_altitude_illness_normal():
    res = hape_hace_evaluator.evaluate_altitude_illness(
        headache_severity=0,
        gastrointestinal_nausea=0,
        fatigue_weakness=0,
        dizziness_lightheadedness=0,
    )
    assert res["lake_louise_score"] == 0
    assert res["immediate_descent_required"] is False
