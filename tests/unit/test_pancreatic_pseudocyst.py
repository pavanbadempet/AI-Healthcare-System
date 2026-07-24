"""
Unit tests for Pancreatic Pseudocyst Drainage Engine
"""

from backend.ml.pancreatic_pseudocyst_drainage_engine import pseudocyst_engine


def test_evaluate_won_drainage():
    res = pseudocyst_engine.evaluate_pfc_drainage_eligibility(
        collection_max_diameter_cm=8.5,
        encapsulation_duration_weeks=5.0,
        necrotic_debris_percent=25.0,
        symptomatic_gastric_outlet_obstruction=True,
    )
    assert res["drainage_indicated"] is True
    assert res["pfc_type"] == "WALLED_OFF_NECROSIS_WON"
    assert "DIRECT_ENDOSCOPIC_NECROSECTOMY" in res["recommended_drainage_modality"]


def test_evaluate_immature_pfc():
    res = pseudocyst_engine.evaluate_pfc_drainage_eligibility(
        collection_max_diameter_cm=7.0,
        encapsulation_duration_weeks=2.0,  # immature < 4 weeks
    )
    assert res["drainage_indicated"] is False
    assert res["recommended_drainage_modality"] == "OBSERVATION"
