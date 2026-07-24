"""
Unit tests for Chronic HDV High-Dose Bulevirtide Engine
"""

from backend.ml.hdv_triple_combination_bulevirtide_engine import hdv_triple_engine


def test_evaluate_hdv_triple_high_dose():
    res = hdv_triple_engine.evaluate_hdv_triple_therapy(
        hdv_rna_iu_mL=1500000.0,
        compensated_cirrhosis_present=True,
    )
    assert res["bulevirtide_daily_dose_mg"] == 10.0
    assert res["triple_combination_indicated"] is True
    assert "TRIPLE THERAPY" in res["recommended_regimen"]


def test_evaluate_hdv_standard_2mg():
    res = hdv_triple_engine.evaluate_hdv_triple_therapy(
        hdv_rna_iu_mL=80000.0,
        compensated_cirrhosis_present=False,
    )
    assert res["bulevirtide_daily_dose_mg"] == 2.0
    assert res["triple_combination_indicated"] is False
