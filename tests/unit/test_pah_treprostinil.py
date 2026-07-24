"""
Unit tests for PAH Treprostinil Titration Engine
"""

from backend.ml.pah_treprostinil_titration_engine import treprostinil_engine


def test_evaluate_treprostinil_titrate_up():
    res = treprostinil_engine.evaluate_treprostinil_titration(
        current_breaths_per_session=3,
        who_functional_class=3,
        cough_or_flushing_tolerable=True,
    )
    assert res["titration_status"] == "TITRATE_UP_BY_1_BREATH"
    assert res["recommended_next_breaths_per_session"] == 4
    assert res["target_breaths_per_session"] == 12


def test_evaluate_treprostinil_intolerable_decrease():
    res = treprostinil_engine.evaluate_treprostinil_titration(
        current_breaths_per_session=6,
        who_functional_class=2,
        cough_or_flushing_tolerable=False,
    )
    assert res["titration_status"] == "DECREASE_DOSE_FOR_TOLERABILITY"
    assert res["recommended_next_breaths_per_session"] == 5
