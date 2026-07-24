"""
Unit tests for Ranson Pancreatitis Engine
"""

from backend.ml.ranson_pancreatitis_engine import ranson_pancreatitis_engine


def test_calculate_ranson_score_high():
    res = ranson_pancreatitis_engine.calculate_ranson_score(
        age_years=62,
        wbc_count_10_3_ul=18.5,
        blood_glucose_mg_dL=240.0,
        ast_u_l=280.0,
        ldh_u_l=420.0,
        hematocrit_drop_percent_48h=12.0,
        bun_rise_mg_dL_48h=6.5,
        serum_calcium_mg_dL_48h=7.2,
    )
    assert res["ranson_total_score"] == 8
    assert res["estimated_mortality_percent"] == 50.0
    assert res["severe_pancreatitis_present"] is True
    assert res["icu_admission_indicated"] is True
    assert "STAT ICU admission" in res["clinical_recommendation"]


def test_calculate_ranson_score_low():
    res = ranson_pancreatitis_engine.calculate_ranson_score(
        age_years=35,
        wbc_count_10_3_ul=9.0,
        blood_glucose_mg_dL=110.0,
        ast_u_l=45.0,
        ldh_u_l=180.0,
    )
    assert res["ranson_total_score"] == 0
    assert res["estimated_mortality_percent"] == 1.0
    assert res["severe_pancreatitis_present"] is False
