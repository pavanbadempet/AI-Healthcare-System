"""
Unit tests for TIMI NSTEMI Score Engine
"""

from backend.ml.timi_nstemi_score import timi_engine


def test_calculate_timi_score_high():
    res = timi_engine.calculate_timi_score(
        age_65_or_older=True,
        three_or_more_cad_risk_factors=True,
        known_cad_stenosis_50pct_or_more=True,
        aspirin_use_past_7_days=True,
        severe_angina_past_24h=True,
        st_deviation_0_5mm_or_more=True,
        elevated_cardiac_markers=True,
    )
    assert res["timi_score"] == 7
    assert res["risk_category"] == "HIGH_RISK"
    assert "Coronary Angiography" in res["clinical_recommendation"]


def test_calculate_timi_score_low():
    res = timi_engine.calculate_timi_score(
        age_65_or_older=False,
        three_or_more_cad_risk_factors=False,
        known_cad_stenosis_50pct_or_more=False,
        aspirin_use_past_7_days=False,
        severe_angina_past_24h=False,
        st_deviation_0_5mm_or_more=False,
        elevated_cardiac_markers=False,
    )
    assert res["timi_score"] == 0
    assert res["risk_category"] == "LOW_RISK"
