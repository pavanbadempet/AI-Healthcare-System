"""
Unit tests for Generalized Myasthenia Gravis Rozanolixizumab Dosing Engine
"""

from backend.ml.gmg_rozanolixizumab_dosing_engine import rozanolixizumab_engine


def test_evaluate_rozanolixizumab_standard_weight():
    res = rozanolixizumab_engine.evaluate_rozanolixizumab_dosing(
        patient_weight_kg=72.0,
        total_igg_level_mg_dL=750.0,
        achr_or_musk_antibody_positive=True,
    )
    assert res["eligible_for_rozanolixizumab"] is True
    assert res["weekly_dose_mg"] == 560
    assert "ONCE_WEEKLY_FOR_6_WEEKS" in res["treatment_cycle"]


def test_evaluate_rozanolixizumab_low_igg_hold():
    res = rozanolixizumab_engine.evaluate_rozanolixizumab_dosing(
        patient_weight_kg=60.0,
        total_igg_level_mg_dL=150.0,  # Below 200 mg/dL threshold
    )
    assert res["eligible_for_rozanolixizumab"] is False
