"""
Tier 2: Boundary & Corner Cases — Clinical Calculators Exhaustive Boundary Matrix
Tests mathematical limits, clamping behavior, division-by-zero resilience, and extreme clinical edge values.
"""
import pytest
from backend.rust_bridge import RustBridgeEngine


def test_framingham_extreme_boundaries(bridge: RustBridgeEngine = None):
    """Tests Framingham risk calculation with boundary and extreme patient values."""
    b = bridge or RustBridgeEngine()
    score_young = b.calculate_framingham_rust(age=20.0, total_chol=150.0, hdl_chol=50.0, sbp=110.0, smoker=False)
    score_old = b.calculate_framingham_rust(age=85.0, total_chol=320.0, hdl_chol=25.0, sbp=210.0, smoker=True)
    assert isinstance(score_young, float)
    assert isinstance(score_old, float)
    assert 0.0 <= score_young <= 100.0
    assert 0.0 <= score_old <= 100.0
    assert score_old > score_young


def test_fib4_zero_and_negative_platelets(bridge: RustBridgeEngine = None):
    """Verifies that FIB-4 handles zero or negative platelets and ALT without ZeroDivisionError."""
    b = bridge or RustBridgeEngine()
    res_zero = b.calculate_fib4_rust(ast=50.0, alt=40.0, platelets=0.0, age=45.0)
    assert res_zero == 0.0

    res_neg = b.calculate_fib4_rust(ast=50.0, alt=-10.0, platelets=150.0, age=45.0)
    assert res_neg == 0.0


def test_meld_clamping_and_dialysis_override(bridge: RustBridgeEngine = None):
    """Verifies that MELD score enforces statutory lower (6.0) and upper (40.0) bounds and dialysis rules."""
    b = bridge or RustBridgeEngine()
    score_min = b.calculate_meld_rust(bilirubin_mg_dl=0.2, inr=0.8, creatinine_mg_dl=0.5, on_dialysis=False)
    assert score_min >= 6.0

    score_dialysis = b.calculate_meld_rust(bilirubin_mg_dl=3.0, inr=2.0, creatinine_mg_dl=1.0, on_dialysis=True)
    score_nodialysis = b.calculate_meld_rust(bilirubin_mg_dl=3.0, inr=2.0, creatinine_mg_dl=1.0, on_dialysis=False)
    assert score_dialysis > score_nodialysis

    score_max = b.calculate_meld_rust(bilirubin_mg_dl=35.0, inr=9.0, creatinine_mg_dl=12.0, on_dialysis=True)
    assert score_max <= 40.0


def test_ascvd_age_boundary_cutoff(bridge: RustBridgeEngine = None):
    """Verifies that ASCVD risk estimator safely handles out-of-range age inputs (<20 and >79)."""
    b = bridge or RustBridgeEngine()
    score_pediatric = b.calculate_ascvd_rust(
        age=15.0, total_chol=180.0, hdl_chol=50.0, sbp=110.0,
        treated_bp=False, smoker=False, diabetic=False, is_female=True
    )
    assert score_pediatric == 0.0

    score_centenarian = b.calculate_ascvd_rust(
        age=88.0, total_chol=180.0, hdl_chol=50.0, sbp=110.0,
        treated_bp=False, smoker=False, diabetic=False, is_female=True
    )
    assert score_centenarian == 0.0


def test_egfr_zero_and_negative_inputs(bridge: RustBridgeEngine = None):
    """Verifies that CKD-EPI eGFR handles zero/negative creatinine or age without crashing."""
    b = bridge or RustBridgeEngine()
    res_zero_cr = b.compute_rust_egfr(serum_creatinine=0.0, age=45.0, is_female=False)
    assert res_zero_cr == 0.0

    res_neg_age = b.compute_rust_egfr(serum_creatinine=1.0, age=-5.0, is_female=False)
    assert res_neg_age == 0.0


def test_qsofa_boundary_decision_thresholds(bridge: RustBridgeEngine = None):
    """Verifies exact threshold cutoffs for qSOFA sepsis criteria (RR=22, SBP=100, GCS=15)."""
    b = bridge or RustBridgeEngine()
    score_sub, _ = b.compute_sepsis_qsofa_rust(resp_rate=21.0, sbp=101.0, gcs=15.0)
    assert score_sub == 0

    score_thresh, risk = b.compute_sepsis_qsofa_rust(resp_rate=22.0, sbp=100.0, gcs=14.0)
    assert score_thresh == 3
    assert risk == "HIGH_SEPSIS_RISK"
