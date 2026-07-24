"""
Unit tests for LAAC Watchman vs Amulet Sizing Engine
"""

from backend.ml.laac_watchman_amulet_sizing_engine import laac_engine


def test_evaluate_laac_eligible():
    res = laac_engine.evaluate_laac_sizing(
        laa_ostium_max_diameter_mm=22.0,
        laa_usable_depth_mm=18.0,
        nonvalvular_afib_present=True,
        cha2ds2_vasc_score=4,
        has_bled_score=3,
    )
    assert res["laac_eligible"] is True
    assert res["device_selected"] == "WATCHMAN_FLX"
    assert res["recommended_device_size_mm"] == 25.3
    assert "ELIGIBLE FOR LAAC PROCEDURE" in res["clinical_recommendation"]


def test_evaluate_laac_thrombus_contraindicated():
    res = laac_engine.evaluate_laac_sizing(
        laa_ostium_max_diameter_mm=22.0,
        laa_usable_depth_mm=18.0,
        laa_thrombus_present_on_tee=True,
    )
    assert res["laac_eligible"] is False
    assert res["reason"] == "LAA_THROMBUS_STRICT_CONTRAINDICATION"
    assert "LAAC STRICTLY CONTRAINDICATED" in res["clinical_recommendation"]
