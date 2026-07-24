"""
Unit tests for Clinical Discharge Summarizer Agent
"""

from backend.agents.discharge_summarizer_agent import discharge_summarizer


def test_generate_discharge_summary_agent():
    res = discharge_summarizer.generate_discharge_summary(
        patient_id=42,
        patient_name="John Doe",
        admission_date="2026-07-15",
        discharge_date="2026-07-22",
        primary_diagnosis="Hypertensive Emergency",
        discharge_medications=["Amlodipine 5mg", "Lisinopril 10mg"],
        followup_days=5,
    )
    assert res["status"] == "COMPLETED"
    assert "John Doe" in res["discharge_summary_text"]
    assert len(res["red_flag_warnings"]) > 0
    assert res["fhir_document_reference"]["resourceType"] == "DocumentReference"
