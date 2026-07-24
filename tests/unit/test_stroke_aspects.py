"""
Unit tests for Stroke ASPECTS Evaluator
"""

from backend.ml.stroke_aspects_evaluator import stroke_aspects_evaluator


def test_evaluate_aspects_score_high():
    res = stroke_aspects_evaluator.evaluate_aspects_score(
        subcortical_hypodensity_regions=["Lentiform"],
        cortical_hypodensity_regions=["M1"],
    )
    assert res["aspects_score"] == 8
    assert res["endovascular_thrombectomy_eligible"] is True
    assert "Stat Endovascular Thrombectomy" in res["clinical_recommendation"]


def test_evaluate_aspects_score_low():
    res = stroke_aspects_evaluator.evaluate_aspects_score(
        subcortical_hypodensity_regions=["Caudate", "Lentiform", "Internal Capsule", "Insular ribbon"],
        cortical_hypodensity_regions=["M1", "M2", "M3"],
    )
    assert res["aspects_score"] == 3
    assert res["endovascular_thrombectomy_eligible"] is False
