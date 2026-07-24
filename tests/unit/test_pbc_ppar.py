"""
Unit tests for PBC PPAR Agonist Eligibility Engine
"""

from backend.ml.pbc_ppar_agonist_eligibility_engine import pbc_ppar_engine


def test_evaluate_pbc_seladelpar_eligible():
    res = pbc_ppar_engine.evaluate_pbc_ppar_eligibility(
        alkaline_phosphatase_u_L=240.0,
        alp_upper_limit_normal_u_L=116.0,  # ~2.07x ULN
        udca_adequate_trial_12_months=True,
        pruritus_moderate_to_severe=True,
    )
    assert res["eligible_for_ppar_agonist"] is True
    assert res["recommended_ppar_agent"] == "SELADELPAR_10MG_DAILY"
    assert "ELIGIBLE FOR SECOND-LINE PPAR AGONIST" in res["clinical_recommendation"]


def test_evaluate_pbc_adequate_response():
    res = pbc_ppar_engine.evaluate_pbc_ppar_eligibility(
        alkaline_phosphatase_u_L=130.0,
        alp_upper_limit_normal_u_L=116.0,  # ~1.12x ULN
        total_bilirubin_mg_dL=0.8,
    )
    assert res["eligible_for_ppar_agonist"] is False
