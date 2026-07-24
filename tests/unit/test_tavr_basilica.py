"""
Unit tests for TAVR BASILICA Coronary Obstruction Engine
"""

from backend.ml.tavr_basilica_coronary_obstruction_engine import basilica_engine


def test_evaluate_basilica_indicated():
    res = basilica_engine.evaluate_coronary_obstruction_risk(
        vtc_distance_left_main_mm=3.2,
        coronary_height_left_main_mm=8.5,
        failed_bioprosthesis_present=True,
    )
    assert res["high_risk_coronary_obstruction"] is True
    assert res["recommended_prevention_technique"] == "BASILICA_LEAFLET_LACERATION"
    assert "BASILICA" in res["clinical_recommendation"]


def test_evaluate_low_risk_tavr():
    res = basilica_engine.evaluate_coronary_obstruction_risk(
        vtc_distance_left_main_mm=6.5,
        coronary_height_left_main_mm=13.0,
    )
    assert res["high_risk_coronary_obstruction"] is False
    assert res["recommended_prevention_technique"] == "STANDARD_TAVR_NO_CORONARY_PROTECTION"
