"""
Unit tests for Autoimmune Hepatitis IAIHG Engine
"""

from backend.ml.autoimmune_hepatitis_iaihg_engine import aih_iaihg_engine


def test_evaluate_definite_aih():
    res = aih_iaihg_engine.evaluate_simplified_iaihg_score(
        ana_or_sma_titer="TITER_1_80_OR_HIGHER",
        serum_igg_level="ELEVATED_1_10_TIMES_ULN",
        histology_features="TYPICAL",
        viral_hepatitis_excluded=True,
    )
    assert res["iaihg_score"] == 8
    assert res["diagnosis"] == "DEFINITE_AUTOIMMUNE_HEPATITIS"
    assert res["immunosuppressive_therapy_indicated"] is True


def test_evaluate_unlikely_aih():
    res = aih_iaihg_engine.evaluate_simplified_iaihg_score(
        ana_or_sma_titer="NEGATIVE",
        serum_igg_level="NORMAL",
        histology_features="ATYPICAL",
        viral_hepatitis_excluded=True,
    )
    assert res["iaihg_score"] == 2
    assert res["diagnosis"] == "UNLIKELY_AUTOIMMUNE_HEPATITIS"
