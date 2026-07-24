"""
Unit tests for TPVR Pulmonary Valve Sizing Engine
"""

from backend.ml.tpvr_pulmonary_valve_sizing_engine import tpvr_engine


def test_evaluate_harmony_candidate():
    res = tpvr_engine.evaluate_tpvr_eligibility(
        rvot_max_diameter_mm=24.5,
        pulmonary_regurgitation_fraction_pct=42.0,
        rvedvi_mL_m2=165.0,
        conduit_type="NATIVE_RVOT",
    )
    assert res["tpvr_eligible"] is True
    assert res["recommended_valve"] == "HARMONY_TPV_22MM"
    assert res["recommended_size_mm"] == 22


def test_evaluate_coronary_compression_risk():
    res = tpvr_engine.evaluate_tpvr_eligibility(
        rvot_max_diameter_mm=22.0,
        pulmonary_regurgitation_fraction_pct=40.0,
        rvedvi_mL_m2=160.0,
        coronary_compression_risk=True,
    )
    assert res["tpvr_eligible"] is False
    assert res["recommended_valve"] == "INELIGIBLE"
