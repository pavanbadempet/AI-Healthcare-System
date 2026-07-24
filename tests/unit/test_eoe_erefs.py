"""
Unit tests for EoE EREFS Score Engine
"""

from backend.ml.eoe_erefs_score_engine import eoe_erefs_engine


def test_calculate_erefs_score_severe():
    res = eoe_erefs_engine.calculate_erefs_score(
        edema_score_0_to_1=1,
        rings_trachealisation_score_0_to_3=3,
        exudates_score_0_to_2=2,
        furrows_score_0_to_2=1,
        stricture_diameter_score_0_to_1=1,
    )
    assert res["total_erefs_score"] == 8
    assert res["remodeling_stage"] == "SEVERE_FIBROSTENOTIC_EOE"
    assert res["dupilumab_biologic_indicated"] is True
    assert res["esophageal_balloon_dilatation_indicated"] is True
    assert "Dupilumab" in res["clinical_recommendation"]


def test_calculate_erefs_score_mild():
    res = eoe_erefs_engine.calculate_erefs_score(
        edema_score_0_to_1=1,
        rings_trachealisation_score_0_to_3=0,
        exudates_score_0_to_2=0,
        furrows_score_0_to_2=1,
        stricture_diameter_score_0_to_1=0,
    )
    assert res["total_erefs_score"] == 2
    assert res["remodeling_stage"] == "MILD_INFLAMMATORY_EOE"
    assert res["dupilumab_biologic_indicated"] is False
    assert res["esophageal_balloon_dilatation_indicated"] is False
