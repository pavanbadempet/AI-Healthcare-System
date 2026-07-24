"""
Unit tests for Truelove & Witts UC Engine
"""

from backend.ml.truelove_witts_uc_engine import truelove_witts_engine


def test_classify_uc_severity_severe():
    res = truelove_witts_engine.classify_uc_severity(
        bloody_stools_per_day=8,
        pulse_rate_bpm=105,
        temperature_celsius=38.2,
        hemoglobin_g_dL=9.8,
        esr_mm_hr=45.0,
    )
    assert res["uc_severity_grade"] == "SEVERE_FULMINANT_ULCERATIVE_COLITIS"
    assert res["systemic_toxicity_present"] is True
    assert res["inpatient_iv_steroid_rescue_indicated"] is True
    assert "IV Hydrocortisone" in res["clinical_recommendation"]


def test_classify_uc_severity_mild():
    res = truelove_witts_engine.classify_uc_severity(
        bloody_stools_per_day=2,
    )
    assert res["uc_severity_grade"] == "MILD_ULCERATIVE_COLITIS"
    assert res["inpatient_iv_steroid_rescue_indicated"] is False
