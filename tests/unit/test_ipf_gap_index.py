"""
Unit tests for IPF GAP Index Model
"""

from backend.ml.ipf_gap_index_model import ipf_gap_model


def test_calculate_gap_stage_stage3():
    res = ipf_gap_model.calculate_gap_stage(
        male_gender=True,
        age_years=68,
        fvc_percent_predicted=45.0,
        dlco_percent_predicted=30.0,
    )
    assert res["gap_total_points"] == 8
    assert res["gap_stage"] == "STAGE_III"
    assert res["one_year_mortality_percent"] == 39.0
    assert res["lung_transplantation_eval_indicated"] is True


def test_calculate_gap_stage_stage1():
    res = ipf_gap_model.calculate_gap_stage(
        male_gender=False,
        age_years=58,
        fvc_percent_predicted=82.0,
        dlco_percent_predicted=70.0,
    )
    assert res["gap_total_points"] == 0
    assert res["gap_stage"] == "STAGE_I"
    assert res["lung_transplantation_eval_indicated"] is False
