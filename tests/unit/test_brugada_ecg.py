"""
Unit tests for Brugada ECG Classifier
"""

from backend.ml.brugada_ecg_classifier import brugada_classifier


def test_classify_brugada_type1():
    res = brugada_classifier.classify_brugada_pattern(
        st_elevation_v1_v3_mm=2.5,
        pattern_morphology="COVED_TYPE_1",
        syncope_history=True,
    )
    assert res["brugada_pattern_type"] == "BRUGADA_TYPE_1_COVED"
    assert res["sudden_cardiac_death_risk_tier"] == "HIGH_RISK"
    assert res["icd_implantation_recommended"] is True


def test_classify_brugada_normal():
    res = brugada_classifier.classify_brugada_pattern(
        st_elevation_v1_v3_mm=0.5,
        pattern_morphology="NORMAL",
    )
    assert res["brugada_pattern_type"] == "NO_BRUGADA_PATTERN"
    assert res["icd_implantation_recommended"] is False
