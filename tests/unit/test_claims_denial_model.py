"""
Unit tests for Medical Claims Denial Risk AI Predictor
"""

from backend.ml.claims_denial_risk_model import claims_denial_model


def test_predict_claim_denial_risk_low():
    res = claims_denial_model.predict_claim_denial_risk(
        cpt_codes=["99214"],
        icd10_codes=["E11.9"],
        total_billed_amount=150.0,
        has_prior_authorization=True,
        is_in_network_provider=True,
    )
    assert res["risk_status"] == "LOW_RISK"
    assert res["denial_probability"] < 0.20


def test_predict_claim_denial_risk_high():
    res = claims_denial_model.predict_claim_denial_risk(
        cpt_codes=["74177"],
        icd10_codes=[],
        total_billed_amount=2500.0,
        has_prior_authorization=False,
        is_in_network_provider=False,
    )
    assert res["risk_status"] == "HIGH_DENIAL_RISK"
    assert res["denial_probability"] > 0.60
    assert len(res["flagged_reasons"]) >= 2
