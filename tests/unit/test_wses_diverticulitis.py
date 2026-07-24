"""
Unit tests for WSES Diverticulitis Engine
"""

from backend.ml.wses_diverticulitis_engine import wses_diverticulitis_engine


def test_calculate_wses_score_severe():
    res = wses_diverticulitis_engine.calculate_wses_score(
        ct_stage="STAGE_4_FECAL_PERITONITIS",
        asa_physical_status=4,
        age_years=75,
        immunocompromised_host=True,
    )
    assert res["wses_total_score"] == 15
    assert res["thirty_day_mortality_percent"] == 35.0
    assert res["emergency_laparotomy_indicated"] is True
    assert "Emergency Laparotomy" in res["clinical_recommendation"]


def test_calculate_wses_score_mild():
    res = wses_diverticulitis_engine.calculate_wses_score(
        ct_stage="UNCOMPLICATED",
        asa_physical_status=1,
        age_years=42,
    )
    assert res["wses_total_score"] == 0
    assert res["emergency_laparotomy_indicated"] is False
