"""
Unit tests for Chronic HBV Stopping Rules Engine
"""

from backend.ml.hbv_treatment_stopping_rules_engine import hbv_stopping_engine


def test_evaluate_stopping_cirrhosis_contraindicated():
    res = hbv_stopping_engine.evaluate_nuc_withdrawal_safety(
        liver_cirrhosis_present=True,
        hbsag_loss_achieved=True,
    )
    assert res["safe_to_stop_nuc"] is False
    assert res["reason"] == "LIVER_CIRRHOSIS_STRICT_CONTRAINDICATION"
    assert "DO NOT DISCONTINUE NUC ANTIVIRAL THERAPY" in res["clinical_recommendation"]


def test_evaluate_stopping_safe_functional_cure():
    res = hbv_stopping_engine.evaluate_nuc_withdrawal_safety(
        liver_cirrhosis_present=False,
        hbsag_loss_achieved=True,
    )
    assert res["safe_to_stop_nuc"] is True
    assert res["reason"] == "FUNCTIONAL_CURE_HBSAG_LOSS_ACHIEVED"
    assert "SAFE TO CEASE NUC ANTIVIRAL THERAPY" in res["clinical_recommendation"]
