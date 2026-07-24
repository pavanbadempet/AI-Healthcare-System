"""
Unit tests for IIH Dandy Criteria Engine
"""

from backend.ml.iih_dandy_criteria_engine import iih_dandy_engine


def test_evaluate_iih_dandy_criteria_positive():
    res = iih_dandy_engine.evaluate_iih_dandy_criteria(
        lumbar_puncture_opening_pressure_cm_h2o=32.0,
        normal_csf_composition_and_cytology=True,
        papilledema_present_on_fundoscopy=True,
        normal_mri_brain_no_mass_lesion=True,
        mrv_venous_sinus_thrombosis_excluded=True,
    )
    assert res["modified_dandy_criteria_met"] is True
    assert res["iih_diagnosis"] == "IDIOPATHIC_INTRACRANIAL_HYPERTENSION"
    assert res["acetazolamide_and_weight_loss_indicated"] is True
    assert "Acetazolamide" in res["clinical_recommendation"]


def test_evaluate_iih_dandy_criteria_negative():
    res = iih_dandy_engine.evaluate_iih_dandy_criteria(
        lumbar_puncture_opening_pressure_cm_h2o=18.0,
        normal_csf_composition_and_cytology=True,
        papilledema_present_on_fundoscopy=False,
        normal_mri_brain_no_mass_lesion=True,
        mrv_venous_sinus_thrombosis_excluded=True,
    )
    assert res["modified_dandy_criteria_met"] is False
    assert res["iih_diagnosis"] == "OTHER_INTRACRANIAL_PATHOLOGY"
