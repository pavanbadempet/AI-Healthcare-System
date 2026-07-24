"""
Unit tests for IMR Coronary Microvascular Engine
"""

from backend.ml.imr_coronary_microvascular_engine import imr_coronary_engine


def test_evaluate_microvascular_function_positive():
    res = imr_coronary_engine.evaluate_microvascular_function(
        distal_pressure_hyperemia_pd_mmHg=85.0,
        mean_transit_time_hyperemia_sec=0.38,
        coronary_flow_reserve_cfr=1.7,
    )
    assert res["index_of_microvascular_resistance_imr"] == 32.3
    assert res["coronary_microvascular_dysfunction_cmd"] is True
    assert res["anoca_inoca_phenotype"] == "STRUCTURAL_AND_FUNCTIONAL_CMD"
    assert "ANOCA/INOCA Confirmed" in res["clinical_recommendation"]


def test_evaluate_microvascular_function_normal():
    res = imr_coronary_engine.evaluate_microvascular_function(
        distal_pressure_hyperemia_pd_mmHg=80.0,
        mean_transit_time_hyperemia_sec=0.22,
        coronary_flow_reserve_cfr=2.8,
    )
    assert res["index_of_microvascular_resistance_imr"] == 17.6
    assert res["coronary_microvascular_dysfunction_cmd"] is False
    assert res["anoca_inoca_phenotype"] == "NORMAL_MICROVASCULAR_FUNCTION"
