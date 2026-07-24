"""
Unit tests for TAAD Genetic Risk Engine
"""

from backend.ml.taad_genetic_risk_engine import taad_engine


def test_evaluate_marfan_surgery():
    res = taad_engine.evaluate_taad_genetic_risk(
        aortic_root_max_diameter_mm=51.0,
        pathogenic_variant_gene="FBN1",
        family_history_aortic_dissection=True,
    )
    assert res["surgery_indicated"] is True
    assert res["tailored_surgical_threshold_mm"] == 45.0
    assert res["syndrome_name"] == "MARFAN_SYNDROME"


def test_evaluate_loeys_dietz_surgery():
    res = taad_engine.evaluate_taad_genetic_risk(
        aortic_root_max_diameter_mm=43.5,
        pathogenic_variant_gene="TGFBR1",
    )
    assert res["surgery_indicated"] is True
    assert res["tailored_surgical_threshold_mm"] == 42.0
    assert res["syndrome_name"] == "LOEYS_DIETZ_SYNDROME"
