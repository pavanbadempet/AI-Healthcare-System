"""
Unit tests for Alvarado Appendicitis Engine
"""

from backend.ml.appendicitis_alvarado_engine import appendicitis_engine


def test_calculate_alvarado_score_high():
    res = appendicitis_engine.calculate_alvarado_score(
        migration_pain_rlq=True,
        anorexia=True,
        nausea_vomiting=True,
        tenderness_rlq=True,
        rebound_tenderness=True,
        elevated_temperature_37_3C=True,
        leukocytosis_wbc_over_10k=True,
        shift_to_left_neutrophils_over_75pct=True,
    )
    assert res["alvarado_score"] == 10
    assert res["appendicitis_probability_category"] == "HIGH_PROBABILITY"
    assert res["surgical_consult_indicated"] is True


def test_calculate_alvarado_score_low():
    res = appendicitis_engine.calculate_alvarado_score(
        migration_pain_rlq=False,
        anorexia=False,
        nausea_vomiting=False,
        tenderness_rlq=False,
        rebound_tenderness=False,
        elevated_temperature_37_3C=False,
        leukocytosis_wbc_over_10k=False,
        shift_to_left_neutrophils_over_75pct=False,
    )
    assert res["alvarado_score"] == 0
    assert res["appendicitis_probability_category"] == "LOW_PROBABILITY"
    assert res["surgical_consult_indicated"] is False
