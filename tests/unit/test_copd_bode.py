"""
Unit tests for COPD BODE Index Engine
"""

from backend.ml.copd_bode_index_engine import copd_bode_engine


def test_calculate_bode_index_high():
    res = copd_bode_engine.calculate_bode_index(
        body_mass_index=20.0,
        fev1_percent_predicted=30.0,
        mmrc_dyspnea_grade=4,
        six_minute_walk_distance_meters=140.0,
    )
    assert res["bode_index_score"] == 10
    assert res["four_year_mortality_percent"] == 80.0
    assert res["high_mortality_risk"] is True
    assert "triple inhaler" in res["clinical_recommendation"]


def test_calculate_bode_index_low():
    res = copd_bode_engine.calculate_bode_index(
        body_mass_index=26.0,
        fev1_percent_predicted=75.0,
        mmrc_dyspnea_grade=1,
        six_minute_walk_distance_meters=420.0,
    )
    assert res["bode_index_score"] == 0
    assert res["four_year_mortality_percent"] == 18.0
    assert res["high_mortality_risk"] is False
