"""
Unit tests for Chronic Hepatitis B Phase Classifier Engine
"""

from backend.ml.hepatitis_b_phase_classifier_engine import hbv_engine


def test_classify_hbeag_negative_hepatitis():
    res = hbv_engine.classify_hbv_phase(
        hbeag_positive=False,
        hbv_dna_iu_mL=15_000.0,
        alt_u_L=78.0,
        upper_limit_normal_alt=35.0,
    )
    assert res["hbv_phase"] == "HBEAG_NEGATIVE_CHRONIC_HBV_HEPATITIS"
    assert res["antiviral_indicated"] is True
    assert "TENOFOVIR_ALAFENAMIDE" in res["recommended_antiviral"]


def test_classify_inactive_carrier():
    res = hbv_engine.classify_hbv_phase(
        hbeag_positive=False,
        hbv_dna_iu_mL=450.0,
        alt_u_L=22.0,
        upper_limit_normal_alt=35.0,
    )
    assert res["hbv_phase"] == "HBEAG_NEGATIVE_CHRONIC_HBV_INFECTION_INACTIVE_CARRIER"
    assert res["antiviral_indicated"] is False
