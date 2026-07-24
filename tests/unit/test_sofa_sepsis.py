"""
Unit tests for SOFA Sepsis Evaluator
"""

from backend.ml.sofa_sepsis_evaluator import sofa_evaluator


def test_calculate_sofa_score_severe_sepsis():
    res = sofa_evaluator.calculate_sofa_score(
        pao2_fio2_ratio=180.0,
        platelets_k_uL=45,
        bilirubin_mg_dL=3.2,
        mean_arterial_pressure_mmHg=60.0,
        vasopressor_required=True,
        gcs_score=11,
        creatinine_mg_dL=2.8,
    )
    assert res["sofa_score"] >= 12
    assert res["sepsis_organ_failure_present"] is True
    assert res["estimated_icu_mortality_percent"] > 40.0


def test_calculate_sofa_score_normal():
    res = sofa_evaluator.calculate_sofa_score(
        pao2_fio2_ratio=450.0,
        platelets_k_uL=220,
        bilirubin_mg_dL=0.8,
        mean_arterial_pressure_mmHg=85.0,
        vasopressor_required=False,
        gcs_score=15,
        creatinine_mg_dL=0.9,
    )
    assert res["sofa_score"] == 0
    assert res["sepsis_organ_failure_present"] is False
