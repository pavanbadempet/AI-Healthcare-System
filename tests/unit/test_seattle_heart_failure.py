"""
Unit tests for Seattle Heart Failure Model
"""

from backend.ml.seattle_heart_failure_model import shfm_model


def test_calculate_shfm_survival_high_risk():
    res = shfm_model.calculate_shfm_survival(
        nyha_class=4,
        ejection_fraction_percent=20,
        systolic_bp_mmHg=98,
        sodium_mEq_L=130.0,
        hemoglobin_g_dL=10.5,
        on_beta_blocker=False,
        on_acei_arb_arni=False,
        on_aldosterone_antagonist=False,
    )
    assert res["shfm_risk_score"] >= 3.0
    assert res["one_year_survival_probability_percent"] < 80.0
    assert res["guideline_triple_therapy_active"] is False


def test_calculate_shfm_survival_low_risk():
    res = shfm_model.calculate_shfm_survival(
        nyha_class=1,
        ejection_fraction_percent=50,
        systolic_bp_mmHg=125,
        sodium_mEq_L=140.0,
        hemoglobin_g_dL=14.5,
    )
    assert res["shfm_risk_score"] == 0.0
    assert res["one_year_survival_probability_percent"] == 98.0
    assert res["guideline_triple_therapy_active"] is True
