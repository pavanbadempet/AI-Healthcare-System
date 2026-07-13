import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from backend import auth, models
from backend.agents.advisory_board import ClinicalAdvisoryBoard


def _create_user(db_session, username: str, role: str, facility_id: int | None = None) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        full_name=f"{role.title()} User",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        allow_data_collection=1,
        facility_id=facility_id,
        gender=1,
        dob="1980-05-15"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def _create_facility(db_session, name: str) -> models.HospitalFacility:
    facility = models.HospitalFacility(
        name=name,
        facility_type="hospital",
        country="US",
        region="CA",
        status="active",
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)
    return facility

@pytest.mark.asyncio
@patch("backend.agents.advisory_board.generate")
async def test_advisory_board_execution_success(mock_generate, db_session):
    """Verify advisory board agent runs sequential debate, uses vitals, and logs CareEvent."""
    facility = _create_facility(db_session, "Heart & Endocrine Center")
    patient = _create_user(db_session, "patient_advisory", "patient", facility_id=facility.id)

    # Seed latest vital observation
    vitals = models.VitalObservation(
        patient_id=patient.id,
        heart_rate=82.0,
        systolic_bp=135.0,
        diastolic_bp=88.0,
        spo2=96.0,
        temperature_c=37.1,
        respiratory_rate=18.0,
        observed_at=datetime.now(timezone.utc)
    )
    db_session.add(vitals)

    # Seed recent HealthRecord
    record = models.HealthRecord(
        user_id=patient.id,
        record_type="heart",
        prediction="High Risk (0.78)",
        timestamp=datetime.now(timezone.utc)
    )
    db_session.add(record)
    db_session.commit()

    # Mock the LLM outputs for each round
    cardio_opinion = "Cardiologist: Patient has mild hypertension and elevated heart rate."
    endo_opinion = "Endocrinologist: Possible insulin resistance, watch metabolic markers."
    cardio_rebuttal = "Cardiologist Rebuttal: Agree with metabolic markers but prioritize cardiovascular risk."
    endo_rebuttal = "Endocrinologist Rebuttal: Agree, glycemic control will also help CV risk."
    gp_synthesis = json.dumps({
        "consensus_note": "A clear correlation between hypertension and metabolic syndrome was identified. Initiate lifestyle modifications and low-dose ACE inhibitor.",
        "icd10_codes": ["I10", "E11.9"],
        "lifestyle_plan": ["Reduce sodium intake", "30 mins moderate exercise daily"],
        "treatment_plan": ["Lisinopril 5mg daily", "Follow-up HbA1c in 3 months"]
    })

    mock_generate.side_effect = [
        cardio_opinion,
        endo_opinion,
        cardio_rebuttal,
        endo_rebuttal,
        gp_synthesis
    ]

    agent = ClinicalAdvisoryBoard(db_session)
    result = await agent.execute_board(patient.id)

    # Assert success and structure of output
    assert result["status"] == "success"
    assert result["patient_id"] == patient.id
    assert "HR: 82.0 bpm" in result["patient_vitals_context"]
    assert "BP: 135.0/88.0 mmHg" in result["patient_vitals_context"]

    # Verify rounds
    debate = result["debate"]
    assert debate["round1"]["cardiologist"] == cardio_opinion
    assert debate["round1"]["endocrinologist"] == endo_opinion
    assert debate["round2"]["cardiologist_rebuttal"] == cardio_rebuttal
    assert debate["round2"]["endocrinologist_rebuttal"] == endo_rebuttal

    synthesis = debate["round3"]["coordinator_synthesis"]
    assert synthesis["consensus_note"] == "A clear correlation between hypertension and metabolic syndrome was identified. Initiate lifestyle modifications and low-dose ACE inhibitor."
    assert "I10" in synthesis["icd10_codes"]
    assert "Lisinopril 5mg daily" in synthesis["treatment_plan"]

    # Verify CareEvent was logged
    care_event = db_session.query(models.CareEvent).filter(
        models.CareEvent.patient_id == patient.id,
        models.CareEvent.event_type == "advisory_board_consensus"
    ).first()
    assert care_event is not None
    assert "Consensus: A clear correlation" in care_event.summary
    assert "ICD-10 Codes: I10, E11.9" in care_event.summary

    # Verify generate calls
    assert mock_generate.call_count == 5
    call_args = mock_generate.call_args_list
    # Check that context with vitals and recent prediction is passed in
    first_call_prompt = call_args[0][1]["prompt"]
    assert "Heart Rate: 82.0 bpm" in first_call_prompt
    assert "Heart Prediction: High Risk (0.78)" in first_call_prompt


@pytest.mark.asyncio
async def test_advisory_board_patient_not_found(db_session):
    """Verify advisory board returns error if patient does not exist."""
    agent = ClinicalAdvisoryBoard(db_session)
    result = await agent.execute_board(9999)
    assert "error" in result
    assert result["error"] == "Patient not found"


@pytest.mark.asyncio
@patch("backend.agents.advisory_board.generate")
async def test_advisory_board_gp_synthesis_fallback(mock_generate, db_session):
    """Verify GP synthesis falls back to raw string when JSON is malformed."""
    facility = _create_facility(db_session, "Fallback Clinic")
    patient = _create_user(db_session, "patient_fallback", "patient", facility_id=facility.id)

    mock_generate.side_effect = [
        "Cardio Opinion",
        "Endo Opinion",
        "Cardio Rebuttal",
        "Endo Rebuttal",
        "This is not a valid JSON structure synthesis."
    ]

    agent = ClinicalAdvisoryBoard(db_session)
    result = await agent.execute_board(patient.id)

    assert result["status"] == "success"
    synthesis = result["debate"]["round3"]["coordinator_synthesis"]
    assert "This is not a valid JSON structure synthesis." in synthesis["consensus_note"]


@pytest.mark.asyncio
@patch("backend.agents.advisory_board.generate")
async def test_advisory_board_api_access_control(mock_generate, client, db_session):
    """Verify endpoint GET /v1/predict/advisory-board/{patient_id} access control."""
    facility = _create_facility(db_session, "Access Test Facility")
    patient = _create_user(db_session, "patient_access", "patient", facility_id=facility.id)
    doctor_assigned = _create_user(db_session, "doctor_assigned", "doctor", facility_id=facility.id)
    doctor_unassigned = _create_user(db_session, "doctor_unassigned", "doctor", facility_id=facility.id)
    admin = _create_user(db_session, "admin_user", "admin", facility_id=facility.id)

    # Assign doctor to patient via appointment
    appt = models.Appointment(
        user_id=patient.id,
        doctor_id=doctor_assigned.id,
        date_time=datetime(2026, 6, 25, 10, 0, tzinfo=timezone.utc),
        status="Scheduled"
    )
    db_session.add(appt)
    db_session.commit()

    # Capture ORM values before HTTP calls (client fixture closes session)
    patient_id = patient.id
    assigned_username = doctor_assigned.username
    unassigned_username = doctor_unassigned.username
    admin_username = admin.username
    patient_username = patient.username

    # Pre-generate all tokens
    token_assigned = auth.create_access_token({"sub": assigned_username})
    token_admin = auth.create_access_token({"sub": admin_username})
    token_unassigned = auth.create_access_token({"sub": unassigned_username})
    token_patient = auth.create_access_token({"sub": patient_username})

    url = f"/v1/predict/advisory-board/{patient_id}"

    # Mock the debate outputs to prevent actual LLM call
    mock_generate.side_effect = [
        "Cardio Opinion", "Endo Opinion", "Cardio Rebuttal", "Endo Rebuttal",
        json.dumps({"consensus_note": "Approved", "icd10_codes": [], "lifestyle_plan": [], "treatment_plan": []})
    ]

    # 1. Assigned Doctor should succeed
    response = client.get(url, headers={"Authorization": f"Bearer {token_assigned}"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Reset mock side_effect for next call
    mock_generate.side_effect = [
        "Cardio Opinion", "Endo Opinion", "Cardio Rebuttal", "Endo Rebuttal",
        json.dumps({"consensus_note": "Approved", "icd10_codes": [], "lifestyle_plan": [], "treatment_plan": []})
    ]

    # 2. Admin should succeed
    response = client.get(url, headers={"Authorization": f"Bearer {token_admin}"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 3. Unassigned Doctor should fail (403)
    response = client.get(url, headers={"Authorization": f"Bearer {token_unassigned}"})
    assert response.status_code == 403
    assert "Doctor is not assigned to this patient" in response.json()["detail"]

    # 4. Patient should fail (403)
    response = client.get(url, headers={"Authorization": f"Bearer {token_patient}"})
    assert response.status_code == 403
    assert "Doctor or admin privileges required" in response.json()["detail"]

