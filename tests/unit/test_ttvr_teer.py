"""
Unit tests for TTVR EVOQUE vs TEER Decision Engine
"""

from backend.ml.ttvr_evoque_vs_teer_decision_engine import ttvr_teer_engine


def test_evaluate_ttvr_evoque_large_gap():
    res = ttvr_teer_engine.evaluate_ttvr_vs_teer(
        tricuspid_coaptation_gap_mm=9.5,  # Unsuitable for TEER
        leaflet_tethering_height_mm=9.0,
        annulus_perimeter_derived_diameter_mm=45.0,
        severe_or_torrential_tr=True,
    )
    assert res["teer_unsuitable"] is True
    assert res["recommended_strategy"] == "TTVR_EVOQUE_VALVE_REPLACEMENT"
    assert res["evoque_size_mm"] == 48
    assert "TRANSCATHETER TRICUSPID VALVE REPLACEMENT" in res["clinical_recommendation"]


def test_evaluate_tricuspid_teer_small_gap():
    res = ttvr_teer_engine.evaluate_ttvr_vs_teer(
        tricuspid_coaptation_gap_mm=4.0,  # Suitable for TEER
        leaflet_tethering_height_mm=5.0,
        annulus_perimeter_derived_diameter_mm=40.0,
    )
    assert res["teer_unsuitable"] is False
    assert res["recommended_strategy"] == "TRICUSPID_TEER_TRICLIP_PASCAL"
