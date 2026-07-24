"""
Unit tests for HFrEF GDMT Optimizer
"""

from backend.ml.hf_gdmt_optimizer import hf_gdmt_optimizer


def test_evaluate_gdmt_quadruple_therapy_unoptimized():
    res = hf_gdmt_optimizer.evaluate_gdmt_quadruple_therapy(
        ejection_fraction_percent=30,
        systolic_bp_mmHg=115,
        heart_rate_bpm=74,
        egfr_mL_min_1_73m2=65.0,
        potassium_mEq_L=4.2,
        on_arni_acei_arb=True,
        on_beta_blocker=True,
        on_mra=False,
        on_sglt2i=False,
    )
    assert res["active_gdmt_pillar_count"] == 2
    assert res["quadruple_therapy_fully_optimized"] is False
    assert any("SGLT2" in r for r in res["optimization_recommendations"])


def test_evaluate_gdmt_quadruple_therapy_fully_optimized():
    res = hf_gdmt_optimizer.evaluate_gdmt_quadruple_therapy(
        ejection_fraction_percent=28,
        systolic_bp_mmHg=120,
        heart_rate_bpm=68,
        egfr_mL_min_1_73m2=70.0,
        potassium_mEq_L=4.4,
        on_arni_acei_arb=True,
        on_beta_blocker=True,
        on_mra=True,
        on_sglt2i=True,
    )
    assert res["active_gdmt_pillar_count"] == 4
    assert res["quadruple_therapy_fully_optimized"] is True
