"""
Unit tests for ALS Gold Coast Diagnostic Criteria Engine
"""

from backend.ml.als_gold_coast_criteria_engine import als_gold_coast_engine


def test_evaluate_als_gold_coast_confirmed():
    res = als_gold_coast_engine.evaluate_gold_coast_als(
        progressive_motor_impairment=True,
        bulbar_umn_lmn_signs=True,
        cervical_umn_lmn_signs=True,
        emg_denervation_fasciculations_present=True,
    )
    assert res["gold_coast_criteria_met"] is True
    assert res["involved_body_regions_count"] == 2
    assert "RILUZOLE" in res["recommended_pharmacotherapy"]


def test_evaluate_als_sod1_tofersen():
    res = als_gold_coast_engine.evaluate_gold_coast_als(
        progressive_motor_impairment=True,
        cervical_umn_lmn_signs=True,
        sod1_mutation_present=True,
    )
    assert res["gold_coast_criteria_met"] is True
    assert "TOFERSEN" in res["recommended_pharmacotherapy"]
