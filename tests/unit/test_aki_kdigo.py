"""
Unit tests for AKI KDIGO Staging Engine
"""

from backend.ml.aki_kdigo_staging_engine import aki_staging_engine


def test_stage_aki_progression_stage3():
    res = aki_staging_engine.stage_aki_progression(
        baseline_creatinine_mg_dL=1.0,
        current_creatinine_mg_dL=3.2,
        urine_output_mL_kg_hr_past_6hr=0.2,
    )
    assert res["kdigo_aki_stage"] == "STAGE_3_SEVERE_AKI"
    assert "Nephrology Consult" in res["clinical_recommendation"]


def test_stage_aki_progression_stage0():
    res = aki_staging_engine.stage_aki_progression(
        baseline_creatinine_mg_dL=0.9,
        current_creatinine_mg_dL=0.95,
        urine_output_mL_kg_hr_past_6hr=0.8,
    )
    assert res["kdigo_aki_stage"] == "STAGE_0_NO_AKI"
