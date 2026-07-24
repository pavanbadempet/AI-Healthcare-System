"""
Unit tests for TAVR ViV Sizing Engine
"""

from backend.ml.tavr_valve_in_valve_engine import tavr_viv_engine


def test_evaluate_standard_tavr_viv():
    res = tavr_viv_engine.evaluate_tavr_viv_candidacy(
        surgical_valve_model="PERIMOUNT_23",
        true_internal_diameter_mm=20.5,
        coronary_height_left_main_mm=13.5,
        virtual_transcatheter_valve_to_coronary_distance_mm=6.0,
    )
    assert res["coronary_obstruction_risk"] is False
    assert res["basilica_laceration_indicated"] is False
    assert "ELIGIBLE FOR TAVR VALVE-IN-VALVE" in res["clinical_recommendation"]


def test_evaluate_high_risk_coronary_obstruction_basilica():
    res = tavr_viv_engine.evaluate_tavr_viv_candidacy(
        surgical_valve_model="MITROFLOW_21",
        true_internal_diameter_mm=17.5,
        coronary_height_left_main_mm=7.5,
        virtual_transcatheter_valve_to_coronary_distance_mm=2.5,
    )
    assert res["coronary_obstruction_risk"] is True
    assert res["basilica_laceration_indicated"] is True
    assert "HIGH RISK FOR CORONARY OBSTRUCTION" in res["clinical_recommendation"]
    assert "BASILICA" in res["clinical_recommendation"]
