"""
Unit tests for TEER Mitral Clip Feasibility Engine
"""

from backend.ml.teer_mitral_clip_feasibility_engine import teer_engine


def test_evaluate_teer_eligible():
    res = teer_engine.evaluate_teer_mitral_suitability(
        severe_mitral_regurgitation_present=True,
        mitral_valve_area_cm2=4.2,
        posterior_leaflet_length_mm=10.0,
        coaptation_depth_mm=7.0,
        flail_gap_mm=4.0,
    )
    assert res["teer_eligible"] is True
    assert res["recommended_procedure"] == "TRANSCATHETER_EDGE_TO_EDGE_REPAIR_TEER"
    assert "ANATOMICALLY SUITABLE FOR TEER" in res["clinical_recommendation"]


def test_evaluate_teer_ineligible_mva_stenosis():
    res = teer_engine.evaluate_teer_mitral_suitability(
        mitral_valve_area_cm2=2.8,  # Too small
    )
    assert res["teer_eligible"] is False
