"""
Unit tests for MG QMG & MG-ADL Score Engine
"""

from backend.ml.mg_qmg_adl_score_engine import mg_score_engine


def test_evaluate_severe_mg_ravulizumab():
    res = mg_score_engine.evaluate_mg_scores(
        qmg_total_score=18,
        mg_adl_total_score=12,
        achr_antibody_positive=True,
    )
    assert res["mg_severity"] == "SEVERE_MYASTHENIA"
    assert res["targeted_biologic_indicated"] is True
    assert res["recommended_biologic_agent"] == "RAVULIZUMAB_C5_COMPLEMENT_INHIBITOR"


def test_evaluate_mild_mg():
    res = mg_score_engine.evaluate_mg_scores(
        qmg_total_score=4,
        mg_adl_total_score=3,
    )
    assert res["mg_severity"] == "MILD_MYASTHENIA"
    assert res["targeted_biologic_indicated"] is False
