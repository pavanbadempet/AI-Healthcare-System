"""
Unit tests for ACh Vasospasm Engine
"""

from backend.ml.coronary_vasospasm_ach_engine import ach_vasospasm_engine


def test_evaluate_ach_provocation_test_positive():
    res = ach_vasospasm_engine.evaluate_ach_provocation_test(
        max_epicardial_diameter_reduction_percent=95.0,
        ischemic_st_shift_present=True,
        typical_anginal_chest_pain_reproduced=True,
    )
    assert res["epicardial_vasospasm_confirmed"] is True
    assert res["vasospastic_angina_diagnosis"] == "EPICARDIAL_VASOSPASTIC_PRINZMETAL_ANGINA"
    assert res["calcium_channel_blocker_therapy_indicated"] is True
    assert res["avoid_beta_blockers"] is True
    assert "High-Dose Calcium Channel Blockers" in res["clinical_recommendation"]


def test_evaluate_ach_provocation_test_negative():
    res = ach_vasospasm_engine.evaluate_ach_provocation_test(
        max_epicardial_diameter_reduction_percent=20.0,
        ischemic_st_shift_present=False,
        typical_anginal_chest_pain_reproduced=False,
    )
    assert res["epicardial_vasospasm_confirmed"] is False
    assert res["vasospastic_angina_diagnosis"] == "NEGATIVE_ACH_PROVOCATION_TEST"
    assert res["calcium_channel_blocker_therapy_indicated"] is False
