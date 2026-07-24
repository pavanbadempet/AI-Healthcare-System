"""
Unit tests for PAH ESC/ERS 4-Strata Risk Engine
"""

from backend.ml.pah_esc_ers_4strata_risk_engine import pah_4strata_engine


def test_calculate_4strata_low_risk():
    res = pah_4strata_engine.calculate_4strata_risk(
        who_functional_class=1,
        six_minute_walk_distance_m=480.0,
        nt_pro_bnp_pg_mL=150.0,
    )
    assert res["risk_stratum"] == "LOW_RISK"
    assert res["mean_risk_score"] == 1.0


def test_calculate_4strata_high_risk():
    res = pah_4strata_engine.calculate_4strata_risk(
        who_functional_class=4,
        six_minute_walk_distance_m=120.0,
        nt_pro_bnp_pg_mL=1800.0,
    )
    assert res["risk_stratum"] == "HIGH_RISK"
    assert res["mean_risk_score"] == 4.0
    assert "INTRAVENOUS_EPOPROSTENOL" in res["recommended_treatment"]
