"""
Unit tests for Mitral Wilkins Score Engine
"""

from backend.ml.mitral_wilkins_score_engine import mitral_wilkins_engine


def test_calculate_wilkins_score_favorable():
    res = mitral_wilkins_engine.calculate_wilkins_score(
        leaflet_mobility_score=1,
        valvular_thickness_score=2,
        valvular_calcification_score=1,
        subvalvular_thickening_score=2,
    )
    assert res["wilkins_total_score"] == 6
    assert res["ptmc_balloon_valvuloplasty_eligible"] is True
    assert res["recommended_intervention"] == "PERCUTANEOUS_BALLOON_VALVULOPLASTY_PTMC"


def test_calculate_wilkins_score_unfavorable():
    res = mitral_wilkins_engine.calculate_wilkins_score(
        leaflet_mobility_score=3,
        valvular_thickness_score=3,
        valvular_calcification_score=3,
        subvalvular_thickening_score=3,
    )
    assert res["wilkins_total_score"] == 12
    assert res["ptmc_balloon_valvuloplasty_eligible"] is False
    assert "Surgical Mitral Valve Replacement" in res["clinical_recommendation"]
