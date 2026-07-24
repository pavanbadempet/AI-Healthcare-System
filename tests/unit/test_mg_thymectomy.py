"""
Unit tests for MG Thymectomy Eligibility Engine
"""

from backend.ml.mg_thymectomy_eligibility_engine import mg_thymectomy_engine


def test_evaluate_mgtx_eligible():
    res = mg_thymectomy_engine.evaluate_thymectomy_eligibility(
        achr_antibody_positive=True,
        thymoma_present_on_imaging=False,
        age_years=42,
        disease_duration_years=1.5,
        mgfa_class="CLASS_II_MODERATE",
    )
    assert res["mgtx_trial_eligible"] is True
    assert res["thymectomy_indicated"] is True
    assert "ROBOTIC_THYMECTOMY" in res["recommended_surgical_approach"]


def test_evaluate_thymoma_indication():
    res = mg_thymectomy_engine.evaluate_thymectomy_eligibility(
        thymoma_present_on_imaging=True,
        age_years=70,
    )
    assert res["thymoma_indication"] is True
    assert res["thymectomy_indicated"] is True
    assert res["recommended_surgical_approach"] == "EXTENDED_TRANSSTERNAL_THYMECTOMY"
