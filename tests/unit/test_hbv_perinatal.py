"""
Unit tests for Chronic HBV Perinatal Prophylaxis Engine
"""

from backend.ml.hbv_perinatal_prophylaxis_engine import hbv_perinatal_engine


def test_evaluate_maternal_tdf_indicated():
    res = hbv_perinatal_engine.evaluate_perinatal_prophylaxis(
        maternal_hbsag_positive=True,
        gestational_age_weeks=28,
        maternal_hbv_dna_iu_mL=1000000.0,
        maternal_hbeag_positive=True,
    )
    assert res["maternal_tdf_indicated"] is True
    assert "INITIATE MATERNAL TDF PROPHYLAXIS" in res["maternal_recommendation"]
    assert "INFANT HBIG" in res["infant_immunoprophylaxis"]


def test_evaluate_maternal_tdf_not_needed():
    res = hbv_perinatal_engine.evaluate_perinatal_prophylaxis(
        maternal_hbsag_positive=True,
        gestational_age_weeks=28,
        maternal_hbv_dna_iu_mL=500.0,
        maternal_hbeag_positive=False,
    )
    assert res["maternal_tdf_indicated"] is False
