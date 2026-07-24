"""
Unit tests for AIH IAIHG Simplified Engine
"""

from backend.ml.aih_iaihg_simplified_engine import aih_iaihg_engine


def test_calculate_aih_score_definite():
    res = aih_iaihg_engine.calculate_aih_score(
        autoantibodies_ana_or_sma_titer=">=1:80",
        igg_level_relative_to_uln=">1.10x",
        liver_histology_typical_or_compatible="TYPICAL",
        viral_hepatitis_excluded=True,
    )
    assert res["iaihg_total_score"] == 8
    assert res["aih_diagnosis"] == "DEFINITE_AUTOIMMUNE_HEPATITIS"
    assert res["immunosuppressive_therapy_indicated"] is True
    assert "Prednisolone" in res["clinical_recommendation"]


def test_calculate_aih_score_unlikely():
    res = aih_iaihg_engine.calculate_aih_score(
        autoantibodies_ana_or_sma_titer="NONE",
        igg_level_relative_to_uln="NORMAL",
        liver_histology_typical_or_compatible="NONE",
        viral_hepatitis_excluded=False,
    )
    assert res["iaihg_total_score"] == 0
    assert res["aih_diagnosis"] == "UNLIKELY_AIH"
    assert res["immunosuppressive_therapy_indicated"] is False
