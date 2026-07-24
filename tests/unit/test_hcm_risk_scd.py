"""
Unit tests for HCM Risk-SCD 5-Year Mortality Model
"""

from backend.ml.hcm_risk_scd_model import hcm_scd_model


def test_calculate_hcm_scd_risk_high():
    res = hcm_scd_model.calculate_hcm_scd_risk(
        max_lv_wall_thickness_mm=32.0,
        left_atrial_diameter_mm=48.0,
        max_lvot_gradient_mmHg=65.0,
        family_history_scd=True,
        non_sustained_vt=True,
        unexplained_syncope=True,
        age_years=35,
    )
    assert res["five_year_scd_risk_percent"] >= 6.0
    assert res["esc_risk_category"] == "HIGH_RISK"
    assert res["primary_prevention_icd_indicated"] is True


def test_calculate_hcm_scd_risk_low():
    res = hcm_scd_model.calculate_hcm_scd_risk(
        max_lv_wall_thickness_mm=18.0,
        left_atrial_diameter_mm=36.0,
        max_lvot_gradient_mmHg=15.0,
        family_history_scd=False,
        non_sustained_vt=False,
        unexplained_syncope=False,
        age_years=50,
    )
    assert res["five_year_scd_risk_percent"] < 4.0
    assert res["esc_risk_category"] == "LOW_RISK"
    assert res["primary_prevention_icd_indicated"] is False
