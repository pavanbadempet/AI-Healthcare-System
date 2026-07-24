"""
Unit tests for Myasthenic Crisis Extubation Readiness Engine
"""

from backend.ml.myasthenic_crisis_extubation_engine import mg_extubation_engine


def test_evaluate_extubation_ready():
    res = mg_extubation_engine.evaluate_extubation_readiness(
        negative_inspiratory_force_cmH2O=-35.0,
        vital_capacity_mL_kg=18.0,
        maximum_expiratory_pressure_cmH2O=50.0,
        arterial_pco2_mmHg=38.0,
    )
    assert res["extubation_ready"] is True
    assert res["post_extubation_plan"] == "IMMEDIATE_TRANSITION_TO_NIPPV_BIPAP"
    assert "EXTUBATION READINESS MET" in res["clinical_recommendation"]


def test_evaluate_extubation_not_ready():
    res = mg_extubation_engine.evaluate_extubation_readiness(
        negative_inspiratory_force_cmH2O=-18.0,  # Weak
        vital_capacity_mL_kg=11.0,
    )
    assert res["extubation_ready"] is False
    assert res["post_extubation_plan"] == "CONTINUE_MECHANICAL_VENTILATION"
