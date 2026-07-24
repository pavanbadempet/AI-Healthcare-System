"""
Unit tests for Acute UGIB Rockall Score Engine
"""

from backend.ml.ugib_rockall_score_engine import rockall_engine


def test_calculate_rockall_high_risk():
    res = rockall_engine.calculate_full_rockall_score(
        age_years=82,
        pulse_bpm=115.0,
        systolic_bp_mmHg=92.0,
        major_comorbidities="RENAL_FAILURE_LIVER_FAILURE_MALIGNANCY",
        endoscopic_diagnosis="ALL_OTHER_DIAGNOSES",
        stigmata_of_hemorrhage="BLOOD_CLOT_SPURTING_VESSEL",
    )
    assert res["rockall_score"] == 10
    assert res["risk_category"] == "VERY_HIGH_RISK"
    assert "HIGH-RISK ROCKALL SCORE" in res["clinical_recommendation"]


def test_calculate_rockall_low_risk():
    res = rockall_engine.calculate_full_rockall_score(
        age_years=45,
        pulse_bpm=72.0,
        systolic_bp_mmHg=124.0,
    )
    assert res["rockall_score"] == 0
    assert res["risk_category"] == "LOW_RISK"
