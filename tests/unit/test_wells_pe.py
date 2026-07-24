"""
Unit tests for Wells PE Calculator
"""

from backend.ml.wells_pe_calculator import wells_pe_calculator


def test_calculate_wells_pe_score_likely():
    res = wells_pe_calculator.calculate_wells_pe_score(
        clinical_signs_of_dvt=True,
        pe_most_likely_diagnosis=True,
        heart_rate_over_100=True,
        immobilization_or_surgery_past_4wks=False,
        prior_dvt_or_pe=False,
        hemoptysis=False,
        active_cancer=False,
    )
    assert res["wells_score"] == 7.5
    assert res["pe_likely"] is True
    assert res["order_ctpa_immediately"] is True
    assert "CT Pulmonary Angiography" in res["diagnostic_pathway_recommendation"]


def test_calculate_wells_pe_score_unlikely():
    res = wells_pe_calculator.calculate_wells_pe_score(
        clinical_signs_of_dvt=False,
        pe_most_likely_diagnosis=False,
        heart_rate_over_100=False,
        immobilization_or_surgery_past_4wks=False,
        prior_dvt_or_pe=False,
        hemoptysis=True,
        active_cancer=False,
    )
    assert res["wells_score"] == 1.0
    assert res["pe_likely"] is False
    assert res["order_ctpa_immediately"] is False
    assert "D-Dimer" in res["diagnostic_pathway_recommendation"]
