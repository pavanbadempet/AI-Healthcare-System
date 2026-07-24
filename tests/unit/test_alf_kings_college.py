"""
Unit tests for Acute Liver Failure King's College Criteria Engine
"""

from backend.ml.alf_kings_college_criteria_engine import alf_engine


def test_evaluate_apap_kings_college_met():
    res = alf_engine.evaluate_kings_college_criteria(
        acetaminophen_etiology=True,
        arterial_ph=7.22,  # < 7.30
        inr=4.5,
        serum_creatinine_mg_dL=2.8,
        hepatic_encephalopathy_grade=3,
    )
    assert res["kings_college_criteria_met"] is True
    assert res["status_1a_transplant_indicated"] is True
    assert "UNOS Status 1A" in res["clinical_recommendation"]


def test_evaluate_non_apap_inr_met():
    res = alf_engine.evaluate_kings_college_criteria(
        acetaminophen_etiology=False,
        arterial_ph=7.38,
        inr=7.2,  # > 6.5
        serum_creatinine_mg_dL=1.8,
        hepatic_encephalopathy_grade=3,
    )
    assert res["kings_college_criteria_met"] is True
    assert res["status_1a_transplant_indicated"] is True
