"""
Unit tests for Acute Cholangitis Tokyo Guidelines Engine
"""

from backend.ml.acute_cholangitis_tokyo_guidelines_engine import cholangitis_engine


def test_evaluate_tg18_grade_iii_severe():
    res = cholangitis_engine.evaluate_tg18_cholangitis(
        fever_temp_celsius=39.4,
        wbc_count_k_uL=16.5,
        total_bilirubin_mg_dL=6.2,
        organ_dysfunction_shock_or_renal=True,
    )
    assert res["tg18_diagnosis_definite"] is True
    assert res["severity_grade"] == "GRADE_III_SEVERE"
    assert "EMERGENT_ERCP" in res["recommended_ercp_timing"]


def test_evaluate_tg18_grade_i_mild():
    res = cholangitis_engine.evaluate_tg18_cholangitis(
        fever_temp_celsius=38.3,
        wbc_count_k_uL=9.2,
        total_bilirubin_mg_dL=2.4,
    )
    assert res["tg18_diagnosis_definite"] is True
    assert res["severity_grade"] == "GRADE_I_MILD"
