"""
Unit tests for ADHF Pseudo-WRF Engine
"""

from backend.ml.adhf_pseudo_wrf_engine import pseudo_wrf_engine


def test_evaluate_pseudo_wrf():
    res = pseudo_wrf_engine.differentiate_wrf_type(
        baseline_creatinine_mg_dL=1.0,
        current_creatinine_mg_dL=1.4,  # +0.4 mg/dL
        hemoconcentration_present=True,
        nt_probnp_declining=True,
        persistent_congestion_signs=False,
        urine_output_adequate=True,
    )
    assert res["wrf_present"] is True
    assert res["wrf_type"] == "PSEUDO_WRF"
    assert res["diuretic_action"] == "CONTINUE_OR_TITRATE_IV_LOOP_DIURETICS"
    assert "DO NOT WITHDRAW OR REDUCE IV DIURETICS" in res["clinical_recommendation"]


def test_evaluate_true_wrf():
    res = pseudo_wrf_engine.differentiate_wrf_type(
        baseline_creatinine_mg_dL=1.0,
        current_creatinine_mg_dL=1.6,
        hemoconcentration_present=False,
        nt_probnp_declining=False,
        persistent_congestion_signs=True,
        urine_output_adequate=False,
    )
    assert res["wrf_present"] is True
    assert res["wrf_type"] == "TRUE_WRF"
    assert res["diuretic_action"] == "HOLD_OR_REDUCE_DIURETICS_EVALUATE_PERFUSION_AND_INOTROPES"
