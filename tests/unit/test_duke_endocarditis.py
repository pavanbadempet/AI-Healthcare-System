"""
Unit tests for Duke Endocarditis Engine
"""

from backend.ml.duke_endocarditis_engine import duke_endocarditis_engine


def test_evaluate_duke_criteria_definite():
    res = duke_endocarditis_engine.evaluate_duke_criteria(
        major_blood_culture_positive=True,
        major_echo_vegetation_or_abscess=True,
        minor_fever_over_38C=True,
    )
    assert res["duke_classification"] == "DEFINITE_ENDOCARDITIS"
    assert res["empiric_iv_antibiotics_indicated"] is True
    assert "IV bactericidal antibiotic" in res["clinical_recommendation"]


def test_evaluate_duke_criteria_rejected():
    res = duke_endocarditis_engine.evaluate_duke_criteria(
        major_blood_culture_positive=False,
        major_echo_vegetation_or_abscess=False,
        minor_fever_over_38C=True,
    )
    assert res["duke_classification"] == "REJECTED_ENDOCARDITIS"
    assert res["empiric_iv_antibiotics_indicated"] is False
