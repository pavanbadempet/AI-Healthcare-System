"""
Unit tests for Infective Endocarditis Surgical Timing Engine
"""

from backend.ml.endendocarditis_surgical_timing_engine import endocarditis_timing_engine


def test_evaluate_emergency_surgery():
    res = endocarditis_timing_engine.evaluate_surgical_timing(
        refractory_heart_failure_shock=True,
    )
    assert res["surgery_indicated"] is True
    assert res["surgical_timing"] == "EMERGENCY_SURGERY_WITHIN_24_HOURS"


def test_evaluate_urgent_surgery_large_vegetation():
    res = endocarditis_timing_engine.evaluate_surgical_timing(
        vegetation_length_mm=16.0,
        recurrent_embolic_events_on_antibiotics=True,
    )
    assert res["surgery_indicated"] is True
    assert res["surgical_timing"] == "URGENT_SURGERY_WITHIN_7_DAYS"
