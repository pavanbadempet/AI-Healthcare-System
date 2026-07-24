"""
Unit tests for TAVR Valve-in-Valve Engine
"""

from backend.ml.tavr_valve_in_valve_engine import tavr_viv_engine


def test_evaluate_tavr_viv_risk_basilica():
    res = tavr_viv_engine.evaluate_tavr_viv_risk(
        virtual_valve_to_coronary_ostium_distance_vtc_mm=3.2,
        left_coronary_ostium_height_mm=8.5,
        sinus_of_valsalva_diameter_mm=26.0,
        stentless_or_stented_externally_mounted_leaflets=True,
    )
    assert res["high_risk_coronary_occlusion"] is True
    assert res["basilica_leaflet_laceration_indicated"] is True
    assert res["coronary_wire_stent_protection_indicated"] is True
    assert res["viv_risk_phenotype"] == "HIGH_RISK_CORONARY_OBSTRUCTION_PROFILE"
    assert "BASILICA" in res["clinical_recommendation"]


def test_evaluate_tavr_viv_risk_standard():
    res = tavr_viv_engine.evaluate_tavr_viv_risk(
        virtual_valve_to_coronary_ostium_distance_vtc_mm=6.5,
        left_coronary_ostium_height_mm=14.0,
        sinus_of_valsalva_diameter_mm=32.0,
    )
    assert res["high_risk_coronary_occlusion"] is False
    assert res["basilica_leaflet_laceration_indicated"] is False
    assert res["viv_risk_phenotype"] == "STANDARD_TAVR_VIV_PROFILE"
