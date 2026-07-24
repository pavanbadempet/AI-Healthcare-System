"""
Unit tests for Infective Endocarditis Surgical Timing Engine
"""

from backend.ml.endocarditis_surgical_timing_engine import endocarditis_surgical_engine


def test_evaluate_emergency_surgery_refractory_hf():
    res = endocarditis_surgical_engine.evaluate_surgical_timing(
        acute_heart_failure_or_cardiogenic_shock=True,
        perivalvular_abscess_or_fistula=False,
        fungal_endocarditis=False,
        vegetation_size_mm=12.0,
        recurrent_embolic_events=False,
        days_on_adequate_antibiotics=2,
    )
    assert res["is_emergency_indicated"] is True
    assert res["timing_category"] == "EMERGENCY_SURGERY_WITHIN_24H"
    assert "EMERGENCY SURGERY MANDATED" in res["clinical_recommendation"]


def test_evaluate_urgent_surgery_fungal_endocarditis():
    res = endocarditis_surgical_engine.evaluate_surgical_timing(
        acute_heart_failure_or_cardiogenic_shock=False,
        perivalvular_abscess_or_fistula=False,
        fungal_endocarditis=True,
        vegetation_size_mm=8.0,
        recurrent_embolic_events=False,
        days_on_adequate_antibiotics=4,
    )
    assert res["is_urgent_indicated"] is True
    assert res["timing_category"] == "URGENT_SURGERY_WITHIN_7_DAYS"
    assert "URGENT SURGERY MANDATED" in res["clinical_recommendation"]
