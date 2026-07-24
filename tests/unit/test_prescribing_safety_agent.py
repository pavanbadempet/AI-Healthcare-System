"""
Unit tests for Prescribing Safety Agent
"""

from backend.agents.prescribing_safety_agent import prescribing_safety_agent


def test_evaluate_prescription_safe():
    res = prescribing_safety_agent.evaluate_prescription_safety(
        medication_name="Amoxicillin",
        dosage_mg=500,
        egfr=90.0,
        active_medications=["Vitamin D"],
    )
    assert res["safety_status"] == "SAFE"
    assert len(res["warnings"]) == 0


def test_evaluate_prescription_renal_warning():
    res = prescribing_safety_agent.evaluate_prescription_safety(
        medication_name="Metformin",
        dosage_mg=1000,
        egfr=25.0,
        active_medications=[],
    )
    assert res["safety_status"] == "REJECTED"
    assert res["warnings"][0]["type"] == "RENAL_CONTRAINDICATION"


def test_evaluate_prescription_drug_interaction():
    res = prescribing_safety_agent.evaluate_prescription_safety(
        medication_name="Lisinopril",
        dosage_mg=10,
        egfr=80.0,
        active_medications=["Spironolactone"],
    )
    assert res["safety_status"] == "REJECTED"
    assert res["warnings"][0]["type"] == "DRUG_INTERACTION"
