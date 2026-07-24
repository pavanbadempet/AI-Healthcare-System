"""
Unit tests for Myasthenic Crisis & Intubation Decision Engine
"""

from backend.ml.myasthenic_crisis_intubation_engine import mg_crisis_engine


def test_evaluate_imminent_crisis_intubation():
    res = mg_crisis_engine.evaluate_myasthenic_crisis(
        single_breath_count=12,
        forced_vital_capacity_mL_kg=12.0,
        negative_inspiratory_force_cm_H2O=-15.0,
        maximum_expiratory_pressure_cm_H2O=25.0,
    )
    assert res["intubation_indicated"] is True
    assert res["hold_pyridostigmine"] is True
    assert "Elective endotracheal intubation indicated" in res["clinical_recommendation"]


def test_evaluate_stable_neuromuscular():
    res = mg_crisis_engine.evaluate_myasthenic_crisis(
        single_breath_count=35,
        forced_vital_capacity_mL_kg=40.0,
        negative_inspiratory_force_cm_H2O=-55.0,
        maximum_expiratory_pressure_cm_H2O=85.0,
    )
    assert res["intubation_indicated"] is False
    assert res["rule_of_20_30_40_triggered"] is False
