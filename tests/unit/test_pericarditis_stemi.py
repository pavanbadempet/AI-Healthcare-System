"""
Unit tests for Pericarditis vs STEMI ECG Classifier
"""

from backend.ml.pericarditis_stemi_ecg_classifier import pericarditis_stemi_classifier


def test_classify_ecg_stemi():
    res = pericarditis_stemi_classifier.classify_ecg_differential(
        diffuse_concave_st_elevation=False,
        pr_segment_depression_lead_ii=False,
        st_elevation_is_localized_contiguous_leads=True,
        reciprocal_st_depression_present=True,
        troponin_level_ng_mL=4.2,
    )
    assert res["ecg_classification"] == "ACUTE_STEMI_MYOCARDIAL_INFARCTION"
    assert res["cath_lab_activation_required"] is True
    assert "Cath Lab" in res["clinical_recommendation"]


def test_classify_ecg_pericarditis():
    res = pericarditis_stemi_classifier.classify_ecg_differential(
        diffuse_concave_st_elevation=True,
        pr_segment_depression_lead_ii=True,
        st_elevation_is_localized_contiguous_leads=False,
        reciprocal_st_depression_present=False,
        troponin_level_ng_mL=0.08,
    )
    assert res["ecg_classification"] == "ACUTE_PERICARDITIS"
    assert res["cath_lab_activation_required"] is False
    assert "Colchicine" in res["clinical_recommendation"]
