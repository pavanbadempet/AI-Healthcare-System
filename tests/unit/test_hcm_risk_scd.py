"""
Unit tests for HCM Risk-SCD Evaluator
"""

from backend.ml.hcm_risk_scd_evaluator import hcm_scd_evaluator


def test_calculate_hcm_risk_scd_high():
    res = hcm_scd_evaluator.calculate_hcm_risk_scd(
        max_left_ventricular_wall_thickness_mm=32.0,
        left_atrial_diameter_mm=52.0,
        max_lv_outflow_tract_gradient_mmHg=75.0,
        family_history_scd=True,
        non_sustained_ventricular_tachycardia_nsvt=True,
        unexplained_syncope=True,
        age_years=35,
    )
    assert res["five_year_scd_risk_percent"] >= 6.0
    assert res["risk_tier"] == "HIGH_RISK"
    assert res["primary_prevention_icd_indicated"] is True
    assert "Primary Prevention ICD" in res["esc_guideline_recommendation"]


def test_calculate_hcm_risk_scd_low():
    res = hcm_scd_evaluator.calculate_hcm_risk_scd(
        max_left_ventricular_wall_thickness_mm=18.0,
        left_atrial_diameter_mm=35.0,
        max_lv_outflow_tract_gradient_mmHg=15.0,
        family_history_scd=False,
        non_sustained_ventricular_tachycardia_nsvt=False,
        unexplained_syncope=False,
        age_years=60,
    )
    assert res["five_year_scd_risk_percent"] < 4.0
    assert res["risk_tier"] == "LOW_RISK"
    assert res["primary_prevention_icd_indicated"] is False
