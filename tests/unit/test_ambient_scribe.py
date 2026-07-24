"""
Unit tests for AI Ambient Medical Scribe Agent
"""

from backend.agents.ambient_scribe import ambient_scribe

SAMPLE_TRANSCRIPT = """
Patient reports high blood pressure and persistent headache for 3 days.
Vitals: BP 142/90 mmHg, HR 78 bpm, Temp 98.6F.
Impression: Likely essential hypertension exacerbation.
Plan: Prescribe Amlodipine 5mg daily. Recheck BP in 2 weeks.
"""


def test_parse_transcript_to_soap():
    soap = ambient_scribe.parse_transcript_to_soap(SAMPLE_TRANSCRIPT)
    assert "subjective" in soap
    assert "objective" in soap
    assert "assessment" in soap
    assert "plan" in soap
    assert len(soap["extracted_icd10_codes"]) > 0
    assert soap["extracted_icd10_codes"][0]["code"] == "I10"
    assert soap["scribe_confidence"] >= 0.90
