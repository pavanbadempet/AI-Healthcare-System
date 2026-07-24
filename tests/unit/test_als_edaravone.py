"""
Unit tests for ALS Edaravone Eligibility Engine
"""

from backend.ml.als_edaravone_eligibility_engine import edaravone_engine


def test_evaluate_edaravone_oral_eligible():
    res = edaravone_engine.evaluate_edaravone_eligibility(
        alsfrs_r_all_items_score_ge_2=True,
        percent_fvc=88.0,
        disease_duration_years=1.0,
        preferred_formulation="ORAL_SUSPENSION",
    )
    assert res["strict_trial_eligible"] is True
    assert res["recommended_formulation"] == "RADICAVA_ORS_ORAL_SUSPENSION_105MG"
    assert "ELIGIBLE FOR EDARAVONE" in res["clinical_recommendation"]


def test_evaluate_edaravone_low_fvc_ineligible():
    res = edaravone_engine.evaluate_edaravone_eligibility(
        percent_fvc=65.0,  # Below 80% threshold
    )
    assert res["strict_trial_eligible"] is False
