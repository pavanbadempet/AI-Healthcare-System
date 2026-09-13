"""
Tier 1: Feature Coverage — Rust Clinical Calculators & PyO3 CPython FFI (Features 14, 15, 16)
Validates Framingham, FIB-4, MELD, ASCVD, eGFR, qSOFA via Rust FFI and resilient Python fallbacks.
"""
import pytest
from backend.rust_bridge import RustBridgeEngine


def test_clinical_calculator_framingham(bridge: RustBridgeEngine = None):
    """Verifies Framingham 10-Year Cardiovascular Risk Score calculation."""
    b = bridge or RustBridgeEngine()
    score = b.calculate_framingham_rust(
        age=55.0,
        total_chol=240.0,
        hdl_chol=35.0,
        sbp=145.0,
        smoker=True,
    )
    assert isinstance(score, float)
    assert 0.0 <= score <= 100.0
    assert score > 5.0


def test_clinical_calculator_fib4(bridge: RustBridgeEngine = None):
    """Verifies FIB-4 Liver Fibrosis Index calculation."""
    b = bridge or RustBridgeEngine()
    score = b.calculate_fib4_rust(
        ast=65.0,
        alt=45.0,
        platelets=150.0,
        age=52.0,
    )
    assert isinstance(score, float)
    assert score > 0.0
    assert 2.5 <= score <= 4.5


def test_clinical_calculator_meld(bridge: RustBridgeEngine = None):
    """Verifies MELD (Model for End-Stage Liver Disease) Score calculation."""
    b = bridge or RustBridgeEngine()
    score = b.calculate_meld_rust(
        bilirubin_mg_dl=2.5,
        inr=1.8,
        creatinine_mg_dl=1.9,
        on_dialysis=False,
    )
    assert isinstance(score, float)
    assert 6.0 <= score <= 40.0
    assert score >= 15.0


def test_clinical_calculator_ascvd(bridge: RustBridgeEngine = None):
    """Verifies 10-Year ASCVD Risk Estimator calculation."""
    b = bridge or RustBridgeEngine()
    score = b.calculate_ascvd_rust(
        age=62.0,
        total_chol=210.0,
        hdl_chol=42.0,
        sbp=138.0,
        treated_bp=False,
        smoker=False,
        diabetic=True,
        is_female=False,
    )
    assert isinstance(score, float)
    assert 0.1 <= score <= 99.0


def test_clinical_calculator_egfr(bridge: RustBridgeEngine = None):
    """Verifies eGFR (CKD-EPI equation) calculation for male and female patients."""
    b = bridge or RustBridgeEngine()
    egfr_male = b.compute_rust_egfr(serum_creatinine=1.0, age=50.0, is_female=False)
    egfr_female = b.compute_rust_egfr(serum_creatinine=1.0, age=50.0, is_female=True)
    assert isinstance(egfr_male, float)
    assert isinstance(egfr_female, float)
    assert egfr_male > 60.0
    assert egfr_female > 50.0


def test_clinical_calculator_qsofa_sepsis(bridge: RustBridgeEngine = None):
    """Verifies qSOFA Sepsis score computation."""
    b = bridge or RustBridgeEngine()
    score, risk = b.compute_sepsis_qsofa_rust(resp_rate=24.0, sbp=90.0, gcs=13.0)
    assert score == 3
    assert risk == "HIGH_SEPSIS_RISK"

    norm_score, norm_risk = b.compute_sepsis_qsofa_rust(resp_rate=16.0, sbp=120.0, gcs=15.0)
    assert norm_score == 0
    assert "LOW" in norm_risk
