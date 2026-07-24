"""
Unit tests for MG Serogenic Subtype Classification Engine
"""

from backend.ml.mg_serogenic_subtype_classification_engine import mg_subtype_engine


def test_classify_musk_subtype():
    res = mg_subtype_engine.classify_mg_subtype(musk_ab_positive=True)
    assert res["mg_subtype"] == "MUSK_POSITIVE_MG"
    assert res["first_line_targeted_therapy"] == "RITUXIMAB_ANTI_CD20_B_CELL_DEPLETION"


def test_classify_achr_subtype():
    res = mg_subtype_engine.classify_mg_subtype(achr_ab_positive=True)
    assert res["mg_subtype"] == "ACHR_POSITIVE_MG"
    assert "FCRN_ANTAGONISTS" in res["first_line_targeted_therapy"]
