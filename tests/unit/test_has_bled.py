"""
Unit tests for HAS-BLED Calculator
"""

from backend.ml.has_bled_calculator import has_bled_calculator


def test_calculate_has_bled_score_high():
    res = has_bled_calculator.calculate_has_bled_score(
        uncontrolled_hypertension=True,
        abnormal_renal_function=True,
        abnormal_liver_function=False,
        prior_stroke_history=True,
        prior_major_bleeding_history=True,
        labile_inr=False,
        age_over_65=True,
        concomitant_antiplatelet_nsaid=True,
        alcohol_use_excess=False,
    )
    assert res["has_bled_score"] == 6
    assert res["high_bleeding_risk"] is True
    assert res["annual_major_bleeding_risk_percent"] >= 8.7


def test_calculate_has_bled_score_low():
    res = has_bled_calculator.calculate_has_bled_score(
        uncontrolled_hypertension=False,
        abnormal_renal_function=False,
        abnormal_liver_function=False,
        prior_stroke_history=False,
        prior_major_bleeding_history=False,
        labile_inr=False,
        age_over_65=False,
        concomitant_antiplatelet_nsaid=False,
        alcohol_use_excess=False,
    )
    assert res["has_bled_score"] == 0
    assert res["high_bleeding_risk"] is False
    assert res["annual_major_bleeding_risk_percent"] == 1.1
