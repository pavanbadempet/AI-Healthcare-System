"""
Unit tests for LEMS Amifampridine SCLC Screening Engine
"""

from backend.ml.lems_amifampridine_sclc_engine import lems_engine


def test_evaluate_lems_confirmed_and_sclc_screen():
    res = lems_engine.evaluate_lems_management(
        proximal_muscle_weakness_present=True,
        post_exercise_facilitation_present=True,
        autonomic_dysfunction_dry_mouth=True,
        vgcc_antibody_positive=True,
        smoking_history_pack_years=25.0,
        age_years=62.0,
    )
    assert res["lems_confirmed"] is True
    assert res["amifampridine_indicated"] is True
    assert res["high_sclc_risk"] is True
    assert "LAMBERT-EATON MYASTHENIC SYNDROME CONFIRMED" in res["clinical_recommendation"]
    assert "Amifampridine" in res["clinical_recommendation"]
    assert "Small Cell Lung Cancer" in res["clinical_recommendation"]


def test_evaluate_lems_incomplete_criteria():
    res = lems_engine.evaluate_lems_management(
        proximal_muscle_weakness_present=True,
        post_exercise_facilitation_present=False,
        autonomic_dysfunction_dry_mouth=False,
        vgcc_antibody_positive=False,
    )
    assert res["lems_confirmed"] is False
    assert res["amifampridine_indicated"] is False
    assert "EVALUATION INCOMPLETE" in res["clinical_recommendation"]
