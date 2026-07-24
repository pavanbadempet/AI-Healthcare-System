"""
Unit tests for Acute UGIB AIMS65 Mortality Score Engine
"""

from backend.ml.ugib_aims65_mortality_engine import aims65_engine


def test_calculate_aims65_high_risk():
    res = aims65_engine.calculate_aims65_score(
        serum_albumin_g_dL=2.4,
        inr=1.8,
        altered_mental_status=True,
        systolic_bp_mmHg=85.0,
        age_years=72,
    )
    assert res["aims65_score"] == 5
    assert res["risk_category"] == "HIGH_RISK"
    assert res["icu_admission_indicated"] is True


def test_calculate_aims65_low_risk():
    res = aims65_engine.calculate_aims65_score(
        serum_albumin_g_dL=3.8,
        inr=1.1,
        altered_mental_status=False,
        systolic_bp_mmHg=125.0,
        age_years=54,
    )
    assert res["aims65_score"] == 0
    assert res["risk_category"] == "LOW_RISK"
    assert res["icu_admission_indicated"] is False
