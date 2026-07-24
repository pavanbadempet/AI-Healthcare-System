"""
Unit tests for PAH Prostacyclin Pathway Engine
"""

from backend.ml.pah_prostacyclin_pathway_engine import prostacyclin_engine


def test_evaluate_selexipag_titration():
    res = prostacyclin_engine.evaluate_prostacyclin_pathway(
        who_functional_class=2,
        current_oral_selexipag_dose_mcg_bid=400.0,
    )
    assert res["recommended_prostacyclin_agent"] == "ORAL_SELEXIPAG"
    assert res["recommended_next_selexipag_dose_mcg_bid"] == 600.0


def test_evaluate_parenteral_for_class_4():
    res = prostacyclin_engine.evaluate_prostacyclin_pathway(
        who_functional_class=4,
    )
    assert res["recommended_prostacyclin_agent"] == "PARENTERAL_EPOPROSTENOL_OR_TREPROSTINIL"
