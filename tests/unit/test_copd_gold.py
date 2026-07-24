"""
Unit tests for COPD GOLD Classifier
"""

from backend.ml.copd_gold_classifier import copd_gold_classifier


def test_classify_copd_group_e():
    res = copd_gold_classifier.classify_copd(
        fev1_percent_predicted=42.0,
        mmrc_dyspnea_score=3,
        cat_assessment_score=18,
        exacerbations_past_12m=2,
        hospitalizations_past_12m=1,
    )
    assert res["spirometry_gold_grade"] == "GOLD_3_SEVERE"
    assert res["gold_2023_group"] == "GROUP_E"
    assert res["high_exacerbation_risk"] is True
    assert "LABA + LAMA" in res["initial_pharmacotherapy_recommendation"]


def test_classify_copd_group_a():
    res = copd_gold_classifier.classify_copd(
        fev1_percent_predicted=85.0,
        mmrc_dyspnea_score=1,
        cat_assessment_score=6,
        exacerbations_past_12m=0,
        hospitalizations_past_12m=0,
    )
    assert res["spirometry_gold_grade"] == "GOLD_1_MILD"
    assert res["gold_2023_group"] == "GROUP_A"
    assert res["high_exacerbation_risk"] is False
