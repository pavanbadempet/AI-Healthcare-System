"""
Unit tests for Drug Interaction Graph Engine
"""

from backend.ml.drug_interaction_graph import drug_interaction_engine


def test_evaluate_medication_list_alert():
    res = drug_interaction_engine.evaluate_medication_list(["Warfarin", "Aspirin", "Metformin"])
    assert res["interaction_count"] == 1
    assert res["has_major_contraindication"] is True
    assert "bleeding risk" in res["alerts"][0]["effect"]


def test_evaluate_medication_list_safe():
    res = drug_interaction_engine.evaluate_medication_list(["Metformin", "Atorvastatin"])
    assert res["interaction_count"] == 0
    assert res["has_major_contraindication"] is False
