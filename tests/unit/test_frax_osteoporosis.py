"""
Unit tests for FRAX Osteoporosis Calculator
"""

from backend.ml.frax_osteoporosis_calculator import frax_calculator


def test_calculate_fracture_risk_high():
    res = frax_calculator.calculate_fracture_risk(
        age_years=68,
        femoral_neck_t_score=-2.8,
        previous_fracture=True,
        glucocorticoid_use=True,
    )
    assert res["pharmacotherapy_recommended"] is True
    assert res["ten_year_major_osteoporotic_fracture_probability_percent"] >= 20.0
    assert "Bisphosphonate" in res["guideline_action"]


def test_calculate_fracture_risk_low():
    res = frax_calculator.calculate_fracture_risk(
        age_years=52,
        femoral_neck_t_score=-0.5,
    )
    assert res["pharmacotherapy_recommended"] is False
    assert res["ten_year_major_osteoporotic_fracture_probability_percent"] < 20.0
