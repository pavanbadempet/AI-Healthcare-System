"""
Unit tests for MG C5 Complement Inhibitor Dosing Engine
"""

from backend.ml.mg_c5_complement_inhibitor_dosing_engine import c5_inhibitor_engine


def test_evaluate_ravulizumab_eligible():
    res = c5_inhibitor_engine.evaluate_c5_inhibitor_dosing(
        achr_antibody_positive=True,
        meningococcal_vaccination_acwy_and_menb_received=True,
        weeks_since_vaccination=3.0,
        preferred_agent="RAVULIZUMAB",
    )
    assert res["eligible_for_c5_inhibitor"] is True
    assert res["selected_c5_agent"] == "RAVULIZUMAB"
    assert "3300 mg IV every 8 weeks" in res["maintenance_dose_regimen"]


def test_evaluate_c5_inhibitor_unvaccinated_hold():
    res = c5_inhibitor_engine.evaluate_c5_inhibitor_dosing(
        meningococcal_vaccination_acwy_and_menb_received=False,
    )
    assert res["eligible_for_c5_inhibitor"] is False
    assert "CONTRAINDICATED" in res["clinical_recommendation"]
