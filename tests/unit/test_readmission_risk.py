"""
Unit tests for 30-Day Readmission Risk Engine
"""

import pytest
from backend.ml.patient_readmission_risk import ReadmissionRiskEngine, readmission_engine


def test_calculate_readmission_risk_low():
    res = readmission_engine.calculate_readmission_risk(
        length_of_stay_days=2,
        is_acute_admission=False,
        charlson_comorbidity_index=1,
        emergency_visits_past_6m=0,
    )
    assert res["risk_tier"] == "LOW"
    assert res["readmission_probability"] < 0.40


def test_calculate_readmission_risk_high():
    res = readmission_engine.calculate_readmission_risk(
        length_of_stay_days=10,
        is_acute_admission=True,
        charlson_comorbidity_index=5,
        emergency_visits_past_6m=3,
        systolic_bp=175.0,
    )
    assert res["risk_tier"] == "HIGH"
    assert res["readmission_probability"] > 0.60
