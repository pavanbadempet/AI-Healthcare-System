"""
Unit tests for CURB-65 Pneumonia Engine
"""

from backend.ml.curb65_pneumonia_engine import curb65_engine


def test_calculate_curb65_score_icu():
    res = curb65_engine.calculate_curb65_score(
        confusion_present=True,
        bun_mg_dL=24.0,
        respiratory_rate_bpm=32,
        systolic_bp_mmHg=88,
        diastolic_bp_mmHg=55,
        age_years=72,
    )
    assert res["curb65_score"] == 5
    assert res["thirty_day_mortality_risk_percent"] == 27.8
    assert res["icu_admission_indicated"] is True
    assert "ICU admission" in res["triage_recommendation"]


def test_calculate_curb65_score_outpatient():
    res = curb65_engine.calculate_curb65_score(
        confusion_present=False,
        bun_mg_dL=14.0,
        respiratory_rate_bpm=18,
        systolic_bp_mmHg=122,
        diastolic_bp_mmHg=78,
        age_years=45,
    )
    assert res["curb65_score"] == 0
    assert res["inpatient_admission_indicated"] is False
    assert "Outpatient" in res["triage_recommendation"]
