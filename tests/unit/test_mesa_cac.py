"""
Unit tests for MESA CAC Risk Calculator
"""

from backend.ml.mesa_cac_risk_calculator import mesa_cac_calculator


def test_calculate_mesa_cac_risk_high():
    res = mesa_cac_calculator.calculate_mesa_cac_risk(
        agatston_cac_score=450.0,
        age_years=62,
        male_sex=True,
        smoker_current=True,
        diabetes_present=True,
    )
    assert res["ten_year_chd_risk_percent"] >= 7.5
    assert res["statin_and_aspirin_indication"] == "HIGH_INTENSITY_STATIN_AND_ASPIRIN"
    assert "High-Intensity Statin" in res["clinical_recommendation"]


def test_calculate_mesa_cac_risk_zero():
    res = mesa_cac_calculator.calculate_mesa_cac_risk(
        agatston_cac_score=0.0,
        age_years=45,
        male_sex=False,
    )
    assert res["statin_and_aspirin_indication"] == "NOT_INDICATED_CAC_ZERO"
    assert "Defer statin therapy" in res["clinical_recommendation"]
