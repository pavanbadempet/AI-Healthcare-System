from unittest.mock import AsyncMock, patch

import pytest

from backend.assessments import score_assessment, to_fhir_observation
from backend.care_plans import generate_care_plan
from backend.clinical_notes import compile_clinical_note

# ── SOAP/DAP Notes Compiler Tests ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_compile_clinical_note_soap():
    mock_chat_response = (
        "# Clinical SOAP Note\n\n"
        "**Subjective**: Patient reports persistent fatigue.\n"
        "**Objective**: BP is 120/80.\n"
        "**Assessment**: Suspected early signs of diabetes.\n"
        "**Plan**: Order HbA1c screening."
    )

    with patch("backend.clinical_notes.chat", AsyncMock(return_value=mock_chat_response)) as mock_chat:
        result = await compile_clinical_note(
            transcript="Doctor: Tell me what's wrong. Patient: I've been feeling very tired lately, maybe diabetes?",
            format_type="SOAP"
        )

        mock_chat.assert_called_once()
        assert result["format"] == "SOAP"
        assert "Clinical SOAP Note" in result["note_markdown"]
        # Check condition extraction
        detected = result["coded_diagnoses"]
        assert len(detected) == 1
        assert detected[0]["condition"] == "diabetes"
        assert detected[0]["icd10"]["code"] == "E11.9"
        assert detected[0]["snomed"]["code"] == "44054006"


@pytest.mark.asyncio
async def test_compile_clinical_note_dap():
    mock_chat_response = (
        "# Clinical DAP Note\n\n"
        "**Data**: BP 130/90.\n"
        "**Assessment**: Kidney function markers should be monitored.\n"
        "**Plan**: Order renal panel."
    )

    with patch("backend.clinical_notes.chat", AsyncMock(return_value=mock_chat_response)):
        result = await compile_clinical_note(
            transcript="Patient has high blood pressure and worries about kidney health.",
            format_type="DAP"
        )

        assert result["format"] == "DAP"
        detected = result["coded_diagnoses"]
        assert len(detected) == 1
        assert detected[0]["condition"] == "kidney"
        assert detected[0]["icd10"]["code"] == "N18.9"


# ── Outcome Assessment Scoring Tests ────────────────────────────────────────

def test_score_assessment_phq9_minimal():
    res = score_assessment([0, 0, 0, 1, 0, 0, 0, 0, 0], questionnaire_type="PHQ-9")
    assert res["questionnaire"] == "PHQ-9"
    assert res["score"] == 1
    assert res["severity"] == "Minimal or None"
    assert "No active clinical intervention" in res["recommendation"]


def test_score_assessment_phq9_severe():
    res = score_assessment([3, 3, 3, 3, 2, 3, 2, 3, 3], questionnaire_type="PHQ-9")
    assert res["score"] == 25
    assert res["severity"] == "Severe Depression"
    assert "Immediate clinical intervention" in res["recommendation"]


def test_score_assessment_gad7_moderate():
    res = score_assessment([2, 2, 1, 2, 1, 2, 2], questionnaire_type="GAD-7")
    assert res["questionnaire"] == "GAD-7"
    assert res["score"] == 12
    assert res["severity"] == "Moderate Anxiety"


def test_score_assessment_validation_errors():
    # Invalid length
    with pytest.raises(ValueError, match="Expected exactly 9 responses"):
        score_assessment([1, 2, 3], questionnaire_type="PHQ-9")

    # Invalid range values
    with pytest.raises(ValueError, match="between 0 and 3"):
        score_assessment([0, 0, 4, 0, 0, 0, 0, 0, 0], questionnaire_type="PHQ-9")


def test_to_fhir_observation_phq9():
    obs = to_fhir_observation(patient_id="patient-123", score=15, severity="Moderately Severe Depression", questionnaire_type="PHQ-9")
    assert obs["resourceType"] == "Observation"
    assert obs["status"] == "final"
    assert obs["code"]["coding"][0]["code"] == "44249-1"
    assert obs["subject"]["reference"] == "Patient/patient-123"
    assert obs["valueQuantity"]["value"] == 15.0
    assert obs["interpretation"][0]["text"] == "Moderately Severe Depression"


# ── Care Plan Generator Tests ───────────────────────────────────────────────

def test_generate_care_plan_kidney():
    plan = generate_care_plan(patient_id="patient-456", condition="kidney")
    assert plan["resourceType"] == "CarePlan"
    assert plan["status"] == "active"
    assert plan["intent"] == "plan"
    assert "CKD" in plan["title"] or "Kidney" in plan["title"]
    assert len(plan["goal"]) == 2
    assert plan["goal"][0]["lifecycleStatus"] == "active"

    # Check specific kidney activities
    activities = [act["reference"]["display"] for act in plan["activity"]]
    assert "Nephrotoxic Agent Avoidance" in activities
    assert "Renal Diet" in activities


def test_generate_care_plan_fallback():
    plan = generate_care_plan(patient_id="patient-456", condition="unknown-condition")
    assert plan["resourceType"] == "CarePlan"
    assert "General Health Support" in plan["title"]
    activities = [act["reference"]["display"] for act in plan["activity"]]
    assert "Routine Follow-up" in activities
