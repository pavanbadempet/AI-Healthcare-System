"""
Unit tests for MG Complement Inhibitor Engine
"""

from backend.ml.mg_complement_inhibitor_engine import c5_inhibitor_engine


def test_evaluate_c5_inhibitor_cleared():
    res = c5_inhibitor_engine.evaluate_c5_inhibitor_safety(
        achr_antibody_positive=True,
        refractory_gmg_symptoms=True,
        meningococcal_vaccine_acwy_and_menb_given=True,
        vaccine_given_at_least_2_weeks_prior=True,
    )
    assert res["can_proceed"] is True
    assert "RAVULIZUMAB" in res["recommended_c5_agent"]
    assert "CLEARED FOR COMPLEMENT C5 INHIBITOR THERAPY" in res["clinical_recommendation"]


def test_evaluate_c5_inhibitor_vaccine_blocked():
    res = c5_inhibitor_engine.evaluate_c5_inhibitor_safety(
        achr_antibody_positive=True,
        refractory_gmg_symptoms=True,
        meningococcal_vaccine_acwy_and_menb_given=False,
    )
    assert res["safety_clearance"] is False
    assert res["can_proceed"] is False
    assert "NOT cleared; mandate meningococcal vaccines" in res["clinical_recommendation"]
