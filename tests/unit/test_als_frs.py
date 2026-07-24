"""
Unit tests for ALSFRS-R Calculator Engine
"""

from backend.ml.als_frs_r_calculator import alsfrs_r_calculator


def test_calculate_alsfrs_r_score_severe():
    res = alsfrs_r_calculator.calculate_alsfrs_r_score(
        speech_0_to_4=1,
        salivation_0_to_4=2,
        swallowing_0_to_4=1,
        handwriting_0_to_4=2,
        cutting_food_0_to_4=1,
        dressing_hygiene_0_to_4=1,
        turning_in_bed_0_to_4=2,
        walking_0_to_4=1,
        climbing_stairs_0_to_4=0,
        dyspnea_0_to_4=2,
        orthopnea_0_to_4=1,
        respiratory_insufficiency_0_to_4=2,
        disease_duration_months=12.0,
    )
    assert res["total_alsfrs_r_score"] == 16
    assert res["bulbar_subscore"] == 4
    assert res["respiratory_subscore"] == 5
    assert res["progression_rate_pts_per_month"] == 2.67
    assert res["non_invasive_ventilation_niv_indicated"] is True
    assert res["peg_gastrostomy_tube_indicated"] is True
    assert "Urgently initiate Non-Invasive Ventilation" in res["clinical_recommendation"]


def test_calculate_alsfrs_r_score_mild():
    res = alsfrs_r_calculator.calculate_alsfrs_r_score(
        speech_0_to_4=4,
        salivation_0_to_4=4,
        swallowing_0_to_4=4,
        handwriting_0_to_4=4,
        cutting_food_0_to_4=4,
        dressing_hygiene_0_to_4=4,
        turning_in_bed_0_to_4=4,
        walking_0_to_4=4,
        climbing_stairs_0_to_4=4,
        dyspnea_0_to_4=4,
        orthopnea_0_to_4=4,
        respiratory_insufficiency_0_to_4=4,
        disease_duration_months=6.0,
    )
    assert res["total_alsfrs_r_score"] == 48
    assert res["progression_rate_pts_per_month"] == 0.0
    assert res["non_invasive_ventilation_niv_indicated"] is False
    assert res["peg_gastrostomy_tube_indicated"] is False
