"""
Unit tests for ACLF CLIF-C ACLF Score Engine
"""

from backend.ml.aclf_clif_c_aclf_score_engine import clif_aclf_score_engine


def test_calculate_high_clif_c_aclf_score():
    res = clif_aclf_score_engine.calculate_clif_c_aclf_score(
        clif_c_ofs_total=15,
        patient_age_years=62,
        wbc_count_10_3_uL=22.0,
    )
    assert res["clif_c_aclf_score"] >= 64.0
    assert res["estimated_28_day_mortality_percent"] >= 55.0
    assert "CRITICAL CLIF-C ACLF SCORE" in res["clinical_recommendation"]


def test_calculate_low_clif_c_aclf_score():
    res = clif_aclf_score_engine.calculate_clif_c_aclf_score(
        clif_c_ofs_total=7,
        patient_age_years=35,
        wbc_count_10_3_uL=6.0,
    )
    assert res["clif_c_aclf_score"] < 50.0
    assert res["estimated_28_day_mortality_percent"] == 15.0
