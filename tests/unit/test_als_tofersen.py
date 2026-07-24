"""
Unit tests for ALS Tofersen Biomarker Engine
"""

from backend.ml.als_relyvrio_tofersen_biomarker_engine import tofersen_engine


def test_evaluate_tofersen_sod1_positive():
    res = tofersen_engine.evaluate_tofersen_eligibility(
        sod1_mutation_confirmed=True,
        plasma_nfl_pg_mL=70.0,
        post_treatment_nfl_pg_mL=30.0,  # ~57% drop
    )
    assert res["tofersen_indicated"] is True
    assert res["nfl_reduction_percent"] >= 50.0
    assert res["nfl_response"] == "SIGNIFICANT_BIOMARKER_RESPONSE"
    assert "ELIGIBLE FOR TOFERSEN" in res["clinical_recommendation"]


def test_evaluate_tofersen_sod1_negative():
    res = tofersen_engine.evaluate_tofersen_eligibility(
        sod1_mutation_confirmed=False,
    )
    assert res["tofersen_indicated"] is False
