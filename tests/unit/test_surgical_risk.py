"""
Unit tests for Surgical Risk Classifier
"""

from backend.ml.surgical_risk_classifier import surgical_risk_classifier


def test_evaluate_surgical_risk_high():
    res = surgical_risk_classifier.evaluate_surgical_risk(
        asa_class=3,
        high_risk_surgery=True,
        history_ischemic_heart_disease=True,
        history_congestive_heart_failure=False,
        history_cerebrovascular_disease=False,
        preop_creatinine_mg_dL=2.4,
    )
    assert res["rcri_score"] == 3
    assert res["estimated_30day_cardiac_event_risk_percent"] == 5.4
    assert res["clearance_status"] == "HIGH_PERIOPERATIVE_RISK_CARDIOLOGY_CONSULT_REQUIRED"


def test_evaluate_surgical_risk_low():
    res = surgical_risk_classifier.evaluate_surgical_risk(
        asa_class=1,
        high_risk_surgery=False,
        history_ischemic_heart_disease=False,
        history_congestive_heart_failure=False,
        history_cerebrovascular_disease=False,
        preop_creatinine_mg_dL=0.9,
    )
    assert res["rcri_score"] == 0
    assert res["clearance_status"] == "CLEARED_FOR_SURGERY"
