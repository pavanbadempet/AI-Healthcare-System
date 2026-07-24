"""
Unit tests for PAH COMPERA 2.0 Risk Engine
"""

from backend.ml.pah_compera2_risk_engine import compera2_engine


def test_calculate_compera2_low_risk():
    res = compera2_engine.calculate_compera2_risk(
        who_functional_class=1,
        six_minute_walk_distance_m=460.0,
        nt_pro_bnp_pg_mL=120.0,
    )
    assert res["risk_stratum"] == "LOW_RISK"
    assert res["compera2_score"] == 1.0


def test_calculate_compera2_high_risk():
    res = compera2_engine.calculate_compera2_risk(
        who_functional_class=4,
        six_minute_walk_distance_m=140.0,
        nt_pro_bnp_pg_mL=1600.0,
    )
    assert res["risk_stratum"] == "HIGH_RISK"
    assert res["compera2_score"] == 4.0
    assert "UPFRONT_TRIPLE_COMBINATION" in res["recommended_therapy"]
