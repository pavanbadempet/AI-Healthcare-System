"""
Unit tests for FOUR Score Evaluator
"""

from backend.ml.four_score_evaluator import four_score_evaluator


def test_calculate_four_score_severe():
    res = four_score_evaluator.calculate_four_score(
        eye_response_score=0,
        motor_response_score=1,
        brainstem_reflexes_score=1,
        respiration_pattern_score=0,
    )
    assert res["four_total_score"] == 2
    assert res["mortality_risk_tier"] == "EXTREMELY_HIGH"
    assert res["brainstem_reflexes_intact"] is False


def test_calculate_four_score_normal():
    res = four_score_evaluator.calculate_four_score(
        eye_response_score=4,
        motor_response_score=4,
        brainstem_reflexes_score=4,
        respiration_pattern_score=4,
    )
    assert res["four_total_score"] == 16
    assert res["mortality_risk_tier"] == "LOW"
    assert res["brainstem_reflexes_intact"] is True
