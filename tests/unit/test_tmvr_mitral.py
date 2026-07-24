"""
Unit tests for TMVR Mitral Replacement Engine
"""

from backend.ml.tmvr_mitral_replacement_engine import tmvr_engine


def test_evaluate_tmvr_candidate():
    res = tmvr_engine.evaluate_tmvr_eligibility(
        mitral_annulus_perimeter_mm=110.0,
        predicted_neo_lvot_area_cm2=2.2,
        mitral_regurgitation_severity="SEVERE",
        suitable_for_mitraclip_teer=False,
    )
    assert res["tmvr_eligible"] is True
    assert res["recommended_device"] == "TENDYNE_TMVR_MEDIUM_SIZE"
    assert res["neo_lvot_adequate"] is True


def test_evaluate_tmvr_neo_lvot_obstruction_risk():
    res = tmvr_engine.evaluate_tmvr_eligibility(
        mitral_annulus_perimeter_mm=120.0,
        predicted_neo_lvot_area_cm2=1.3,  # < 1.8 cm2
        suitable_for_mitraclip_teer=False,
    )
    assert res["tmvr_eligible"] is False
    assert res["neo_lvot_adequate"] is False
    assert "LAMPOON" in res["clinical_recommendation"]
