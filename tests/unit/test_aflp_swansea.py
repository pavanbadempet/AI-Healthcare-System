"""
Unit tests for AFLP Swansea Criteria Engine
"""

from backend.ml.aflp_swansea_criteria_engine import aflp_engine


def test_evaluate_aflp_diagnosed():
    res = aflp_engine.evaluate_swansea_criteria(
        vomiting_present=True,
        abdominal_pain_present=True,
        hypoglycemia_less_than_4_mmol_L=True,
        elevated_ast_or_alt_over_42_U_L=True,
        elevated_ammonia_over_47_umol_L=True,
        coagulopathy_inr_over_1_4=True,  # 6 features
    )
    assert res["aflp_diagnosed"] is True
    assert res["swansea_criteria_count"] == 6
    assert res["immediate_delivery_indicated"] is True
    assert "CRITICAL OBSTETRIC EMERGENCY" in res["clinical_recommendation"]


def test_evaluate_aflp_not_met():
    res = aflp_engine.evaluate_swansea_criteria(
        vomiting_present=True,
        elevated_ast_or_alt_over_42_U_L=True,  # 2 features
    )
    assert res["aflp_diagnosed"] is False
    assert res["swansea_criteria_count"] == 2
