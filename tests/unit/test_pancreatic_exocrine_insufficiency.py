"""
Unit tests for Pancreatic Exocrine Insufficiency Engine
"""

from backend.ml.pancreatic_exocrine_insufficiency_engine import pei_engine


def test_evaluate_severe_pei():
    res = pei_engine.evaluate_pei_severity(
        fecal_elastase_1_ug_g=45.0,
        steatorrhea_diarrhea_present=True,
        vitamin_d_25_oh_ng_mL=14.0,
    )
    assert res["pei_severity"] == "SEVERE_PANCREATIC_EXOCRINE_INSUFFICIENCY"
    assert res["pert_indicated"] is True
    assert res["recommended_lipase_units_per_meal"] == 75000
    assert res["vitamin_d_deficient"] is True


def test_evaluate_normal_exocrine_function():
    res = pei_engine.evaluate_pei_severity(
        fecal_elastase_1_ug_g=280.0,
    )
    assert res["pei_severity"] == "NORMAL_EXOCRINE_FUNCTION"
    assert res["pert_indicated"] is False
