"""
Unit tests for Acute UGIB Glasgow-Blatchford Score Engine
"""

from backend.ml.ugib_glasgow_blatchford_engine import gbs_engine


def test_calculate_gbs_very_low_risk():
    res = gbs_engine.calculate_gbs(
        bun_mg_dL=12.0,
        hemoglobin_g_dL=14.0,
        systolic_bp_mmHg=125.0,
        heart_rate_bpm=72.0,
        is_female=False,
    )
    assert res["glasgow_blatchford_score"] == 0
    assert res["risk_category"] == "VERY_LOW_RISK"
    assert res["outpatient_discharge_safe"] is True


def test_calculate_gbs_high_risk():
    res = gbs_engine.calculate_gbs(
        bun_mg_dL=35.0,
        hemoglobin_g_dL=8.5,
        systolic_bp_mmHg=88.0,
        heart_rate_bpm=115.0,
        melena_present=True,
        hepatic_disease_history=True,
    )
    assert res["glasgow_blatchford_score"] >= 12
    assert res["risk_category"] == "HIGH_RISK"
    assert res["outpatient_discharge_safe"] is False
