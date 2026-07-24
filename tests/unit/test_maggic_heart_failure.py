"""
Unit tests for Heart Failure MAGGIC Mortality Predictor
"""

from backend.ml.maggic_heart_failure_model import maggic_model


def test_calculate_maggic_mortality_high_risk():
    res = maggic_model.calculate_maggic_mortality(
        ejection_fraction_percent=25,
        nyha_class=4,
        systolic_bp_mmHg=100,
        age_years=72,
        creatinine_mg_dL=2.2,
        on_beta_blocker=False,
        on_acei_arb_arni=False,
    )
    assert res["maggic_score"] >= 25
    assert res["one_year_mortality_risk_percent"] > 20.0
    assert res["guideline_directed_medical_therapy_optimized"] is False


def test_calculate_maggic_mortality_low_risk():
    res = maggic_model.calculate_maggic_mortality(
        ejection_fraction_percent=55,
        nyha_class=1,
        systolic_bp_mmHg=125,
        age_years=54,
        creatinine_mg_dL=0.9,
    )
    assert res["maggic_score"] == 0
    assert res["one_year_mortality_risk_percent"] == 0.0
    assert res["guideline_directed_medical_therapy_optimized"] is True
