"""
Unit tests for SOTA Clinical Logic Engine (backend/sota_clinical_logic.py).
"""

from backend.sota_clinical_logic import (
    RISK_CKD,
    RISK_DIABETES,
    RISK_HEART_DISEASE,
    RISK_HYPERTENSION,
    TrigramSymptomMatcher,
    bitmask_logic,
)


def test_bitmask_composite_risk_evaluation():
    # Normal metrics
    mask, tier = bitmask_logic.evaluate_composite_risk(sbp=120, dbp=80, glucose=90, egfr=90, cholesterol=180)
    assert mask == 0
    assert tier == "OPTIMAL_STABLE"

    # Hypertension + Diabetes
    mask, tier = bitmask_logic.evaluate_composite_risk(sbp=145, dbp=95, glucose=135, egfr=90, cholesterol=180)
    assert mask & RISK_HYPERTENSION
    assert mask & RISK_DIABETES
    assert tier == "MODERATE_ELEVATED"

    # Critical comorbid
    mask, tier = bitmask_logic.evaluate_composite_risk(sbp=150, dbp=100, glucose=140, egfr=45, cholesterol=260)
    assert mask & RISK_HYPERTENSION
    assert mask & RISK_DIABETES
    assert mask & RISK_CKD
    assert mask & RISK_HEART_DISEASE
    assert tier == "CRITICAL_COMORBID"


def test_trigram_symptom_matcher():
    dictionary = ["headache", "chest pain", "shortness of breath", "dizziness"]
    matcher = TrigramSymptomMatcher(dictionary)

    results = matcher.match_symptom("chest pain")
    assert "chest pain" in results
