"""
Unit tests for CIDP INCAT Disability Engine
"""

from backend.ml.cidp_incat_disability_engine import cidp_engine


def test_stage_cidp_ivig_candidate():
    res = cidp_engine.stage_cidp_disability(
        arm_incat_score=2,
        leg_incat_score=2,
        csf_protein_g_L=0.92,
        ncs_demyelinating_features_present=True,
    )
    assert res["cidp_confirmed"] is True
    assert res["total_incat_score"] == 4
    assert res["cidp_severity"] == "MODERATE_CIDP_DISABILITY"
    assert "IVIG_2G_KG" in res["recommended_therapy"]


def test_stage_cidp_refractory():
    res = cidp_engine.stage_cidp_disability(
        arm_incat_score=3,
        leg_incat_score=4,
        csf_protein_g_L=1.15,
        ncs_demyelinating_features_present=True,
        refractory_to_ivig=True,
    )
    assert res["cidp_confirmed"] is True
    assert res["total_incat_score"] == 7
    assert res["cidp_severity"] == "SEVERE_CIDP_DISABILITY"
    assert "FCRN_BLOCKER" in res["recommended_therapy"]
