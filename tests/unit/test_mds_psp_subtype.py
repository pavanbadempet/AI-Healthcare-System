"""
Unit tests for MDS-PSP Tauopathy Subtype Engine
"""

from backend.ml.mds_psp_tauopathy_subtype_engine import psp_subtype_engine


def test_classify_psp_rs():
    res = psp_subtype_engine.classify_psp_subtype(
        vertical_supranuclear_gaze_palsy=True,
        prominent_postural_instability_falls=True,
    )
    assert res["psp_subtype"] == "PSP_RICHARDSON_SYNDROME_PSP_RS"
    assert "4R_TAUOPATHY" in res["associated_pathology"]


def test_classify_psp_cbs():
    res = psp_subtype_engine.classify_psp_subtype(
        asymmetric_limb_apraxia_dystonia=True,
    )
    assert res["psp_subtype"] == "PSP_CORTICOBASAL_SYNDROME_PSP_CBS"
