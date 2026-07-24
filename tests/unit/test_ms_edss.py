"""
Unit tests for Multiple Sclerosis EDSS Calculator
"""

from backend.ml.ms_edss_calculator import ms_edss_calculator


def test_calculate_edss_score_severe():
    res = ms_edss_calculator.calculate_edss_score(
        pyramidal_score=3,
        cerebellar_score=2,
        brainstem_score=1,
        sensory_score=2,
        bowel_bladder_score=1,
        visual_score=0,
        cerebral_score=0,
        ambulation_unassisted_meters=80.0,
    )
    assert res["edss_score"] == 6.5
    assert res["disability_tier"] == "SEVERE_WALKING_IMPAIRMENT_REQUIRES_ASSISTANCE"
    assert res["disease_modifying_therapy_indicated"] is True


def test_calculate_edss_score_mild():
    res = ms_edss_calculator.calculate_edss_score(
        pyramidal_score=1,
        cerebellar_score=0,
        brainstem_score=0,
        sensory_score=0,
        bowel_bladder_score=0,
        visual_score=0,
        cerebral_score=0,
    )
    assert res["edss_score"] == 1.5
    assert res["disability_tier"] == "MILD_DISABILITY"
