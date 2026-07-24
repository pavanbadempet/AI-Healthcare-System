"""
Unit tests for MELD 3.0 Calculator
"""

from backend.ml.meld_3_0_mortality_calculator import meld_3_0_calculator


def test_calculate_meld_3_0_score_high():
    res = meld_3_0_calculator.calculate_meld_3_0_score(
        female_sex=True,
        serum_bilirubin_mg_dL=8.5,
        inr=3.2,
        serum_sodium_mEq_L=128.0,
        serum_creatinine_mg_dL=3.8,
        serum_albumin_g_dL=2.1,
    )
    assert res["meld_3_0_score"] >= 35
    assert res["ninety_day_mortality_risk_percent"] == 80.0
    assert res["transplant_listing_indicated"] is True
    assert "Liver Transplant" in res["clinical_recommendation"]


def test_calculate_meld_3_0_score_low():
    res = meld_3_0_calculator.calculate_meld_3_0_score(
        female_sex=False,
        serum_bilirubin_mg_dL=0.9,
        inr=1.0,
        serum_sodium_mEq_L=140.0,
        serum_creatinine_mg_dL=0.8,
        serum_albumin_g_dL=4.0,
    )
    assert res["meld_3_0_score"] == 11
    assert res["transplant_listing_indicated"] is False
