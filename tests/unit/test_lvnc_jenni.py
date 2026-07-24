"""
Unit tests for LVNC Jenni Criteria Engine
"""

from backend.ml.lvnc_jenni_criteria_engine import lvnc_jenni_engine


def test_evaluate_lvnc_jenni_criteria_positive():
    res = lvnc_jenni_engine.evaluate_lvnc_jenni_criteria(
        nc_c_ratio_end_systole=2.4,
        intertrabecular_recess_flow_color_doppler=True,
        two_layer_myocardial_structure_present=True,
        prominent_trabeculations_apical_lateral=True,
    )
    assert res["jenni_criteria_met"] is True
    assert res["lvnc_diagnosis"] == "LVNC_LEFT_VENTRICULAR_NON_COMPACTION"
    assert res["cardiac_mri_and_anticoagulation_indicated"] is True


def test_evaluate_lvnc_jenni_criteria_negative():
    res = lvnc_jenni_engine.evaluate_lvnc_jenni_criteria(
        nc_c_ratio_end_systole=1.4,
        intertrabecular_recess_flow_color_doppler=False,
        two_layer_myocardial_structure_present=False,
        prominent_trabeculations_apical_lateral=False,
    )
    assert res["jenni_criteria_met"] is False
    assert res["lvnc_diagnosis"] == "NORMAL_OR_OTHER_CARDIOMYOPATHY"
