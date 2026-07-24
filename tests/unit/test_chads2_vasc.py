"""
Unit tests for CHADS2-VASc Calculator
"""

from backend.ml.chads2_vasc_calculator import chads_vasc_calculator


def test_calculate_chads_vasc_score_high():
    res = chads_vasc_calculator.calculate_chads_vasc_score(
        congestive_heart_failure=True,
        hypertension=True,
        age_years=72,
        diabetes_mellitus=True,
        prior_stroke_tia_thromboembolism=True,
        vascular_disease=True,
        female_sex=True,
    )
    assert res["chads_vasc_score"] >= 7
    assert res["annual_ischemic_stroke_risk_percent"] > 10.0
    assert res["oral_anticoagulation_indicated"] is True


def test_calculate_chads_vasc_score_low():
    res = chads_vasc_calculator.calculate_chads_vasc_score(
        congestive_heart_failure=False,
        hypertension=False,
        age_years=45,
        diabetes_mellitus=False,
        prior_stroke_tia_thromboembolism=False,
        vascular_disease=False,
        female_sex=False,
    )
    assert res["chads_vasc_score"] == 0
    assert res["annual_ischemic_stroke_risk_percent"] == 0.2
    assert res["oral_anticoagulation_indicated"] is False
