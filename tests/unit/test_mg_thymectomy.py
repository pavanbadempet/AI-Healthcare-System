"""
Unit tests for MG Thymectomy Eligibility Engine
"""

from backend.ml.mg_thymectomy_eligibility_engine import mg_thymectomy_engine


def test_evaluate_mandatory_thymoma_resection():
    res = mg_thymectomy_engine.evaluate_thymectomy_eligibility(
        thymoma_present_on_ct_mri=True,
        patient_age_years=72,
    )
    assert res["mandatory_for_thymoma"] is True
    assert res["thymectomy_indicated"] is True
    assert "MANDATORY THYMECTOMY FOR THYMOMA" in res["clinical_recommendation"]


def test_evaluate_mgtx_trial_eligible():
    res = mg_thymectomy_engine.evaluate_thymectomy_eligibility(
        thymoma_present_on_ct_mri=False,
        achr_antibody_positive=True,
        generalized_mg_symptoms=True,
        patient_age_years=42,
        disease_duration_years=2.0,
    )
    assert res["mgtx_eligible"] is True
    assert res["thymectomy_indicated"] is True
    assert "THYMECTOMY RECOMMENDED" in res["clinical_recommendation"]
