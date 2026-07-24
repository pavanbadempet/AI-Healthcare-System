"""
Unit tests for ISTH DIC Scoring Engine
"""

from backend.ml.isth_dic_scoring_engine import isth_dic_engine


def test_calculate_isth_dic_score_overt():
    res = isth_dic_engine.calculate_isth_dic_score(
        platelet_count_k_uL=40,
        elevated_fdp_d_dimer="STRONG",
        prolonged_pt_seconds=6.5,
        fibrinogen_g_L=0.8,
    )
    assert res["isth_dic_score"] == 8
    assert res["overt_dic_present"] is True
    assert "Cryoprecipitate" in res["clinical_recommendation"]


def test_calculate_isth_dic_score_non_overt():
    res = isth_dic_engine.calculate_isth_dic_score(
        platelet_count_k_uL=140,
        elevated_fdp_d_dimer="NONE",
        prolonged_pt_seconds=1.0,
        fibrinogen_g_L=2.5,
    )
    assert res["isth_dic_score"] == 0
    assert res["overt_dic_present"] is False
