"""
Unit tests for IPF GAP Mortality Calculator
"""

from backend.ml.ipf_gap_mortality_calculator import ipf_gap_calculator


def test_calculate_ipf_gap_index_stage_iii():
    res = ipf_gap_calculator.calculate_ipf_gap_index(
        male_gender=True,
        age_years=68,
        fvc_percent_predicted=45.0,
        dlco_percent_predicted=30.0,
    )
    assert res["gap_index_score"] == 7
    assert res["gap_stage"] == "GAP_STAGE_III"
    assert res["one_year_mortality_percent"] == 39.0
    assert res["lung_transplant_referral_indicated"] is True
    assert "Lung Transplant Evaluation" in res["clinical_recommendation"]


def test_calculate_ipf_gap_index_stage_i():
    res = ipf_gap_calculator.calculate_ipf_gap_index(
        male_gender=False,
        age_years=58,
        fvc_percent_predicted=82.0,
        dlco_percent_predicted=65.0,
    )
    assert res["gap_index_score"] == 0
    assert res["gap_stage"] == "GAP_STAGE_I"
    assert res["lung_transplant_referral_indicated"] is False
