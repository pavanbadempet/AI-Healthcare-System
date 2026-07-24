"""
Unit tests for NMO AQP4 vs MOGAD Classifier Engine
"""

from backend.ml.nmo_aqp4_mogad_classifier import nmo_classifier_engine


def test_classify_nmosd_aqp4():
    res = nmo_classifier_engine.classify_demyelinating_disorder(
        aqp4_igg_positive=True,
        mog_igg_positive=False,
        letm_segments=4,
        area_postrema_syndrome=True,
    )
    assert res["classification"] == "NMOSD_AQP4_POSITIVE"
    assert res["aqp4_igg_positive"] is True
    assert "Satralizumab" in res["targeted_biologic"]


def test_classify_mogad():
    res = nmo_classifier_engine.classify_demyelinating_disorder(
        aqp4_igg_positive=False,
        mog_igg_positive=True,
        bilateral_optic_neuritis=True,
    )
    assert res["classification"] == "MOGAD_MOG_ANTIBODY_DISEASE"
    assert res["mog_igg_positive"] is True
    assert "IVIG" in res["targeted_biologic"]
