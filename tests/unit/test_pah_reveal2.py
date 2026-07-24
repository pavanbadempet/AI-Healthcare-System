"""
Unit tests for PAH REVEAL 2.0 Risk Score Engine
"""

from backend.ml.pah_reveal2_risk_engine import pah_reveal_engine


def test_calculate_reveal2_low_risk():
    res = pah_reveal_engine.calculate_reveal2_score(
        who_functional_class=1,
        six_minute_walk_distance_m=480.0,
        nt_pro_bnp_pg_mL=150.0,
        right_atrial_pressure_mmHg=8.0,
    )
    assert res["risk_category"] == "LOW_RISK"
    assert res["reveal2_score"] <= 6
    assert "ORAL_DUAL_COMBINATION" in res["recommended_therapy"]


def test_calculate_reveal2_high_risk():
    res = pah_reveal_engine.calculate_reveal2_score(
        who_functional_class=4,
        six_minute_walk_distance_m=140.0,
        nt_pro_bnp_pg_mL=1400.0,
        right_atrial_pressure_mmHg=16.0,
        egfr_mL_min_1_73m2=45.0,
        male_over_60=True,
    )
    assert res["risk_category"] == "HIGH_RISK"
    assert res["reveal2_score"] >= 9
    assert "TRIPLE_COMBINATION" in res["recommended_therapy"]
