"""
Unit tests for TPVR Pulmonary Valve Engine
"""

from backend.ml.tpvr_pulmonary_valve_engine import tpvr_engine


def test_evaluate_tpvr_sapien3_eligible():
    res = tpvr_engine.evaluate_tpvr_suitability(
        rvot_landing_zone_diameter_mm=24.0,
        severe_pulmonary_regurgitation_percent=45.0,
        rv_end_diastolic_volume_index_mL_m2=165.0,
    )
    assert res["tpvr_eligible"] is True
    assert res["recommended_device"] == "EDWARDS_SAPIEN_3_VALVE_20_TO_29MM"
    assert "ELIGIBLE FOR TPVR" in res["clinical_recommendation"]


def test_evaluate_tpvr_coronary_compression_contraindicated():
    res = tpvr_engine.evaluate_tpvr_suitability(
        rvot_landing_zone_diameter_mm=22.0,
        coronary_compression_risk_on_balloon_sizing=True,
    )
    assert res["tpvr_eligible"] is False
    assert "CONTRAINDICATED due to high coronary artery compression" in res["clinical_recommendation"]
