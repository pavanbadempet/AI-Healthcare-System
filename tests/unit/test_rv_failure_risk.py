"""
Unit tests for Invasive RV Failure Risk Score Engine
"""

from backend.ml.rv_failure_risk_score_engine import rvfrs_engine


def test_calculate_rvfrs_score_high():
    res = rvfrs_engine.calculate_rvfrs_score(
        rap_pcwp_ratio=0.72,
        pulmonary_artery_pulsatility_index_papi=1.2,
        preop_vasopressors_count=2,
        preop_ast_u_l=95.0,
    )
    assert res["rvfrs_total_score"] == 6
    assert res["rv_failure_risk_percent"] == 48.0
    assert res["rvad_support_indicated"] is True
    assert "Right Ventricular Assist Device" in res["clinical_recommendation"]


def test_calculate_rvfrs_score_low():
    res = rvfrs_engine.calculate_rvfrs_score(
        rap_pcwp_ratio=0.45,
        pulmonary_artery_pulsatility_index_papi=2.8,
        preop_vasopressors_count=0,
    )
    assert res["rvfrs_total_score"] == 0
    assert res["rv_failure_risk_percent"] == 8.0
    assert res["rvad_support_indicated"] is False
