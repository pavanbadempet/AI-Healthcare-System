"""
Unit tests for ABG Acid-Base Calculator
"""

from backend.ml.abg_acid_base_calculator import abg_calculator


def test_evaluate_abg_high_anion_gap_metabolic_acidosis():
    res = abg_calculator.evaluate_abg(
        ph=7.18,
        paco2_mmHg=28.0,
        hco3_mEq_L=10.0,
        pao2_mmHg=85.0,
        fio2_decimal=0.5,
        sodium_mEq_L=140.0,
        chloride_mEq_L=100.0,
    )
    assert res["primary_acid_base_disorder"] == "METABOLIC_ACIDOSIS"
    assert res["anion_gap"] == 30.0
    assert res["high_anion_gap_acidosis"] is True
    assert res["ards_classification"] == "MODERATE_ARDS"


def test_evaluate_abg_normal():
    res = abg_calculator.evaluate_abg(
        ph=7.40,
        paco2_mmHg=40.0,
        hco3_mEq_L=24.0,
        pao2_mmHg=95.0,
        fio2_decimal=0.21,
    )
    assert res["primary_acid_base_disorder"] == "NORMAL_ACID_BASE"
    assert res["ards_classification"] == "NO_ARDS"
