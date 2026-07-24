"""
Unit tests for Chronic HBV Maternal Transmission Engine
"""

from backend.ml.hepatitis_b_maternal_transmission_engine import hbv_maternal_engine


def test_evaluate_maternal_hbv_pmtct_high_viral_load():
    res = hbv_maternal_engine.evaluate_maternal_hbv_pmtct(
        gestational_age_weeks=26.0,
        hbv_dna_iu_mL=850000.0,
        hbeag_positive=True,
    )
    assert res["pmtct_antiviral_indicated"] is True
    assert res["recommended_antiviral"] == "TDF_300MG_DAILY"
    assert "MATERNAL HBV PROPHYLAXIS INDICATED" in res["clinical_recommendation"]


def test_evaluate_maternal_hbv_pmtct_low_viral_load():
    res = hbv_maternal_engine.evaluate_maternal_hbv_pmtct(
        gestational_age_weeks=26.0,
        hbv_dna_iu_mL=5000.0,
        hbeag_positive=False,
    )
    assert res["pmtct_antiviral_indicated"] is False
    assert res["infant_birth_protocol"] == "HBIG_100IU_IM_PLUS_HBV_VACCINE_WITHIN_12H"
