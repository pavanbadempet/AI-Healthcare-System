"""
Unit tests for MG-ADL Score Engine
"""

from backend.ml.mg_adl_score_engine import mg_adl_engine


def test_calculate_mg_adl_score_severe():
    res = mg_adl_engine.calculate_mg_adl_score(
        talking_score_0_to_3=2,
        chewing_score_0_to_3=2,
        swallowing_score_0_to_3=2,
        breathing_score_0_to_3=2,
        impairment_brushing_teeth_combing_hair_0_to_3=1,
        arising_from_chair_0_to_3=1,
        double_vision_diplopia_0_to_3=2,
        eyelid_droop_ptosis_0_to_3=2,
        achr_antibody_positive=True,
    )
    assert res["total_mg_adl_score"] == 14
    assert res["fcrn_blocker_efgartigimod_indicated"] is True
    assert res["c5_complement_inhibitor_eculizumab_indicated"] is True
    assert "Eculizumab" in res["clinical_recommendation"]


def test_calculate_mg_adl_score_mild():
    res = mg_adl_engine.calculate_mg_adl_score(
        talking_score_0_to_3=0,
        chewing_score_0_to_3=0,
        swallowing_score_0_to_3=1,
        breathing_score_0_to_3=0,
        impairment_brushing_teeth_combing_hair_0_to_3=0,
        arising_from_chair_0_to_3=0,
        double_vision_diplopia_0_to_3=1,
        eyelid_droop_ptosis_0_to_3=1,
    )
    assert res["total_mg_adl_score"] == 3
    assert res["fcrn_blocker_efgartigimod_indicated"] is False
    assert res["c5_complement_inhibitor_eculizumab_indicated"] is False
