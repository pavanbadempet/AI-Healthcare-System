"""
Unit tests for Longitudinal Disease Progression Predictor
"""

from backend.ml.disease_progression_predictor import progression_predictor


def test_predict_ckd_progression_stable():
    res = progression_predictor.predict_ckd_progression(
        historical_egfr=[85.0, 83.0, 82.0],
        historical_years=[2024, 2025, 2026],
    )
    assert res["status"] == "SUCCESS"
    assert res["current_egfr"] == 82.0
    assert res["progression_risk"] == "STABLE"


def test_predict_ckd_progression_rapid():
    res = progression_predictor.predict_ckd_progression(
        historical_egfr=[75.0, 65.0, 55.0],
        historical_years=[2024, 2025, 2026],
    )
    assert res["status"] == "SUCCESS"
    assert res["annual_decline_rate_ml_min"] >= 4.0
    assert res["progression_risk"] == "RAPID_DECLINER"
