"""
Unit tests for TEER Mitral Tricuspid Combination Engine
"""

from backend.ml.teer_mitral_tricuspid_combination_engine import dual_teer_engine


def test_evaluate_simultaneous_dual_teer():
    res = dual_teer_engine.evaluate_dual_teer_strategy(
        mitral_regurgitation_grade=4,
        tricuspid_regurgitation_grade=4,
        systolic_pulmonary_artery_pressure_mmHg=42.0,
        right_ventricular_function_tapse_mm=19.0,
    )
    assert res["teer_strategy"] == "SIMULTANEOUS_DUAL_VALVE_MITRAL_AND_TRICUSPID_TEER"
    assert "MitraClip/PASCAL" in res["clinical_recommendation"]


def test_evaluate_staged_dual_teer():
    res = dual_teer_engine.evaluate_dual_teer_strategy(
        mitral_regurgitation_grade=4,
        tricuspid_regurgitation_grade=4,
        systolic_pulmonary_artery_pressure_mmHg=58.0,
        right_ventricular_function_tapse_mm=14.0,
    )
    assert res["teer_strategy"] == "STAGED_MITRAL_TEER_FIRST_THEN_REEVALUATE_TRICUSPID"
