"""
Unit tests for Chronic HBV Antiviral Resistance Rescue Engine
"""

from backend.ml.hbv_antiviral_resistance_rescue_engine import hbv_resistance_engine


def test_evaluate_lamivudine_resistance_switch_taf():
    res = hbv_resistance_engine.evaluate_rescue_therapy(
        current_nuc_regimen="LAMIVUDINE",
        viral_breakthrough_hbv_dna_iu_mL=15000.0,
        rtM204V_or_I_lamivudine_mutation=True,
    )
    assert res["resistance_or_breakthrough_detected"] is True
    assert res["recommended_rescue_regimen"] == "SWITCH_TO_TENOFOVIR_ALAFENAMIDE_TAF_OR_TDF_MONOTHERAPY"
    assert "SWITCH_TO_TENOFOVIR" in res["clinical_recommendation"]


def test_evaluate_no_resistance():
    res = hbv_resistance_engine.evaluate_rescue_therapy(
        current_nuc_regimen="TAF",
        viral_breakthrough_hbv_dna_iu_mL=20.0,
    )
    assert res["resistance_or_breakthrough_detected"] is False
