"""
Unit tests for GCS TRISS Calculator
"""

from backend.ml.gcs_triss_calculator import gcs_triss_calculator


def test_calculate_gcs_triss_severe():
    res = gcs_triss_calculator.calculate_gcs_triss(
        eye_opening_score=1,
        verbal_response_score=1,
        motor_response_score=2,
        age_years=68,
    )
    assert res["gcs_total_score"] == 4
    assert res["gcs_category"] == "SEVERE_HEAD_INJURY"
    assert res["airway_intubation_indicated"] is True
    assert res["estimated_survival_probability_percent"] < 60.0


def test_calculate_gcs_triss_mild():
    res = gcs_triss_calculator.calculate_gcs_triss(
        eye_opening_score=4,
        verbal_response_score=5,
        motor_response_score=6,
        age_years=32,
    )
    assert res["gcs_total_score"] == 15
    assert res["gcs_category"] == "MILD_HEAD_INJURY"
    assert res["airway_intubation_indicated"] is False
    assert res["estimated_survival_probability_percent"] == 98.0
