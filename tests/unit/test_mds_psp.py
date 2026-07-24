"""
Unit tests for Progressive Supranuclear Palsy MDS-PSP Criteria Engine
"""

from backend.ml.mds_psp_criteria_engine import psp_engine


def test_evaluate_psp_richardson_syndrome():
    res = psp_engine.evaluate_mds_psp_criteria(
        vertical_supranuclear_gaze_palsy=True,
        slow_vertical_saccades=True,
        unprovoked_falls_within_3_years=True,
        parkinsonism_levodopa_resistant=True,
    )
    assert res["psp_criteria_met"] is True
    assert res["psp_phenotype"] == "PROBABLE_PSP_RICHARDSON_SYNDROME_PSP_RS"
    assert "fall prevention" in res["clinical_recommendation"]


def test_evaluate_psp_incomplete():
    res = psp_engine.evaluate_mds_psp_criteria(
        vertical_supranuclear_gaze_palsy=False,
        slow_vertical_saccades=False,
        unprovoked_falls_within_3_years=False,
    )
    assert res["psp_criteria_met"] is False
