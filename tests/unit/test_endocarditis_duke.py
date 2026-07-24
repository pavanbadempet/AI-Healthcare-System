"""
Unit tests for Infective Endocarditis Duke Criteria Engine
"""

from backend.ml.endocarditis_duke_criteria_engine import duke_engine


def test_evaluate_definite_duke_ie():
    res = duke_engine.evaluate_duke_criteria(
        major_blood_culture_positive=True,
        major_echo_or_pet_positive=True,
    )
    assert res["duke_classification"] == "DEFINITE_INFECTIVE_ENDOCARDITIS"
    assert res["empiric_antibiotics_indicated"] is True
    assert "DEFINITE INFECTIVE ENDOCARDITIS" in res["clinical_recommendation"]


def test_evaluate_possible_duke_ie():
    res = duke_engine.evaluate_duke_criteria(
        major_blood_culture_positive=True,
        major_echo_or_pet_positive=False,
        minor_fever_over_38c=True,
    )
    assert res["duke_classification"] == "POSSIBLE_INFECTIVE_ENDOCARDITIS"
