"""
Unit tests for Chronic Hepatitis Delta Bulevirtide Engine
"""

from backend.ml.hepatitis_delta_bulevirtide_engine import hdv_engine


def test_evaluate_bulevirtide_indicated():
    res = hdv_engine.evaluate_hdv_bulevirtide_indication(
        hbsag_positive=True,
        hdv_rna_detected=True,
        hdv_rna_iu_mL=45_000.0,
        alt_u_L=85.0,
        fibrosis_stage_f0_f4=3,
    )
    assert res["bulevirtide_indicated"] is True
    assert "BULEVIR TIDE" in res["recommended_regimen"]


def test_evaluate_bulevirtide_decompensated():
    res = hdv_engine.evaluate_hdv_bulevirtide_indication(
        hbsag_positive=True,
        hdv_rna_detected=True,
        hdv_rna_iu_mL=12_000.0,
        alt_u_L=45.0,
        decompensated_cirrhosis=True,
    )
    assert res["bulevirtide_indicated"] is False
    assert "Liver Transplantation" in res["clinical_recommendation"]
