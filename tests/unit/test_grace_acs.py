"""
Unit tests for GRACE ACS Mortality Predictor
"""

from backend.ml.grace_acs_mortality_model import grace_model


def test_calculate_grace_mortality_high():
    res = grace_model.calculate_grace_mortality(
        age_years=75,
        heart_rate_bpm=115,
        systolic_bp_mmHg=95,
        creatinine_mg_dL=2.2,
        killip_class=3,
        cardiac_arrest_at_admission=True,
    )
    assert res["grace_score"] >= 140
    assert res["risk_category"] == "HIGH_RISK"
    assert res["urgent_coronary_angiography_indicated"] is True


def test_calculate_grace_mortality_low():
    res = grace_model.calculate_grace_mortality(
        age_years=48,
        heart_rate_bpm=72,
        systolic_bp_mmHg=128,
        creatinine_mg_dL=0.9,
        killip_class=1,
    )
    assert res["grace_score"] < 109
    assert res["risk_category"] == "LOW_RISK"
    assert res["urgent_coronary_angiography_indicated"] is False
