"""
Unit tests for Endocarditis Embolic Risk Engine
"""

from backend.ml.endocarditis_embolic_risk_engine import endocarditis_engine


def test_evaluate_emergent_endocarditis_surgery():
    res = endocarditis_engine.evaluate_embolic_risk_and_surgery(
        vegetation_max_length_mm=16.0,
        mobile_vegetation=True,
        staph_aureus_or_fungal_microbiology=True,
        severe_valvular_regurgitation_heart_failure=True,
    )
    assert res["urgent_surgery_indicated"] is True
    assert res["recommended_surgical_timing"] == "EMERGENT_VALVE_SURGERY_WITHIN_24_HOURS"
    assert res["embolic_risk_score"] >= 8


def test_evaluate_conservative_endocarditis():
    res = endocarditis_engine.evaluate_embolic_risk_and_surgery(
        vegetation_max_length_mm=6.0,
        mobile_vegetation=False,
        staph_aureus_or_fungal_microbiology=False,
    )
    assert res["urgent_surgery_indicated"] is False
    assert res["recommended_surgical_timing"] == "CONSERVATIVE_MEDICAL_ANTIMICROBIAL_MANAGEMENT"
