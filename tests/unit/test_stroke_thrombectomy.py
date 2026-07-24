"""
Unit tests for Acute Stroke Extended Window Thrombectomy Engine
"""

from backend.ml.stroke_thrombectomy_extended_window_engine import stroke_evt_engine


def test_evaluate_dawn_defuse3_candidate():
    res = stroke_evt_engine.evaluate_extended_window_evt(
        time_last_known_well_hours=11.0,
        core_infarct_volume_mL=18.0,
        ischemic_penumbra_volume_mL=75.0,
        nihss_score=16,
        lvo_location="ICA_OR_M1",
        age_years=68.0,
    )
    assert res["evt_indicated"] is True
    assert res["dawn_eligible"] is True
    assert res["defuse3_eligible"] is True


def test_evaluate_large_core_ineligible():
    res = stroke_evt_engine.evaluate_extended_window_evt(
        time_last_known_well_hours=10.0,
        core_infarct_volume_mL=95.0,  # core > 70mL
        ischemic_penumbra_volume_mL=110.0,
        nihss_score=18,
    )
    assert res["evt_indicated"] is False
    assert res["dawn_eligible"] is False
    assert res["defuse3_eligible"] is False
