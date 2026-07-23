"""
Unit tests for Medical Coding Auditor Agent
"""

import pytest
from backend.agents.medical_coding_auditor import MedicalCodingAuditorAgent, coding_auditor_agent


def test_audit_coding_accuracy_passed():
    res = coding_auditor_agent.audit_coding_accuracy(
        clinical_note_text="Patient has Type 2 Diabetes managed with metformin.",
        assigned_icd10_codes=["E11.9"],
        assigned_cpt_codes=["99214"],
    )
    assert res["is_compliant"] is True
    assert res["audit_status"] == "PASSED"


def test_audit_coding_accuracy_flagged():
    res = coding_auditor_agent.audit_coding_accuracy(
        clinical_note_text="Routine follow-up for mild headache. Patient has diabetes.",
        assigned_icd10_codes=["R51.9"],  # Missing E11
        assigned_cpt_codes=["99215"],     # Upcoded 99215 without documentation
    )
    assert res["is_compliant"] is False
    assert res["audit_status"] == "AUDIT_FLAGGED"
    assert len(res["findings"]) == 2
