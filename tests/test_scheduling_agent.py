import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend import models
from backend.agents.scheduling_agent import SchedulingAgent


@pytest.fixture
def test_users(db_session):
    """Create test patient and doctor users in the database."""
    run_id = str(uuid.uuid4())[:8]

    patient = models.User(
        username=f"patient_{run_id}",
        email=f"patient_{run_id}@example.com",
        role="patient",
        full_name="Alice Patient",
        facility_id=1
    )

    doctor = models.User(
        username=f"doctor_{run_id}",
        email=f"doctor_{run_id}@example.com",
        role="doctor",
        full_name="Dr. Bob Cardiologist",
        specialization="Cardiologist",
        consultation_fee=600.0,
        facility_id=1
    )

    db_session.add(patient)
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(patient)
    db_session.refresh(doctor)

    return {"patient": patient, "doctor": doctor}

@pytest.fixture(autouse=True)
def mock_rag_by_default():
    """Mock RAG vector store and search globally for all tests."""
    mock_store = MagicMock()
    with patch("backend.rag.get_vector_store", return_value=mock_store) as mock_get_store, \
         patch("backend.rag.search_similar_records", return_value=[]) as mock_search:
        yield mock_get_store, mock_search

@pytest.mark.asyncio
@patch("backend.core_ai.generate")
async def test_agent_chat_booking_success(mock_generate, db_session, test_users):
    """Test that a valid booking action tag executes the database booking successfully."""
    patient = test_users["patient"]
    doctor = test_users["doctor"]

    agent = SchedulingAgent(db_session, patient)

    # Mock the LLM output to return a confirmation message containing the BOOKING_ACTION tag
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    mock_generate.return_value = (
        f"Sure! I can help you book that. Here is the tag: "
        f"[BOOKING_ACTION: doctor_id={doctor.id}, date={tomorrow}, time=10:00, reason=checkup]"
    )

    result = await agent.chat("I want to book an appointment with Dr. Bob tomorrow at 10 AM", [])

    assert result["action_triggered"] is True
    assert result["booking_details"] is not None
    assert result["booking_details"]["doctor_name"] == doctor.full_name
    assert result["error"] is None

    # Verify database entry
    appt = db_session.query(models.Appointment).filter(models.Appointment.user_id == patient.id).first()
    assert appt is not None
    assert appt.doctor_id == doctor.id
    assert "checkup" in appt.reason
    assert "[AI Risk Screen:" in appt.reason
    assert appt.status == "Scheduled"

@pytest.mark.asyncio
@patch("backend.core_ai.generate")
async def test_agent_chat_emergency_warning(mock_generate, db_session, test_users):
    """Test that emergency keywords trigger a warning message."""
    patient = test_users["patient"]
    agent = SchedulingAgent(db_session, patient)

    mock_generate.return_value = "Let me schedule that for you."

    result = await agent.chat("I have severe chest pain and need a doctor", [])

    assert "EMERGENCY WARNING" in result["response"]
    assert "chest pain" in result["response"].lower()

@pytest.mark.asyncio
@patch("backend.core_ai.generate")
async def test_agent_chat_specialty_suggestion(mock_generate, db_session, test_users):
    """Test that clinical keywords trigger specialty suggestions."""
    patient = test_users["patient"]
    agent = SchedulingAgent(db_session, patient)

    mock_generate.return_value = "Which day works for you?"

    result = await agent.chat("I have high blood glucose and need an appointment", [])

    assert "Clinical Suggestion" in result["response"]
    assert "diabetologist" in result["response"].lower()

@pytest.mark.asyncio
@patch("backend.core_ai.generate")
async def test_agent_chat_booking_past_date_fails(mock_generate, db_session, test_users):
    """Test that booking an appointment in the past fails gracefully."""
    patient = test_users["patient"]
    doctor = test_users["doctor"]
    agent = SchedulingAgent(db_session, patient)

    # Book for yesterday
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    mock_generate.return_value = (
        f"[BOOKING_ACTION: doctor_id={doctor.id}, date={yesterday}, time=10:00, reason=checkup]"
    )

    result = await agent.chat("Book yesterday at 10 AM", [])

    assert result["action_triggered"] is True
    assert result["booking_details"] is None
    assert result["error"] is not None
    assert "future" in result["error"].lower()

@pytest.mark.asyncio
@patch("backend.core_ai.generate")
@patch("backend.model_service.model_service.predict_heart")
@patch("backend.model_service.model_service.is_available")
async def test_agent_clinical_screening_heart(mock_is_avail, mock_predict_heart, mock_generate, db_session, test_users):
    """Test that booking with a Cardiologist triggers a Heart Disease pre-screening and attaches results."""
    patient = test_users["patient"]
    doctor = test_users["doctor"] # is a Cardiologist
    agent = SchedulingAgent(db_session, patient)

    # Setup patient dob
    patient.dob = "1980-05-15"
    patient.gender = "Male"
    patient.height = 175.0
    patient.weight = 80.0

    # Create a VitalObservation record in the DB
    vital = models.VitalObservation(
        patient_id=patient.id,
        heart_rate=85.0,
        systolic_bp=135.0,
        diastolic_bp=82.0,
        spo2=98.0,
        observed_at=datetime.now()
    )
    db_session.add(vital)
    db_session.commit()

    # Mock model_service availability and prediction result
    mock_is_avail.return_value = True
    from backend.model_service import PredictionResult
    mock_predict_heart.return_value = PredictionResult(
        prediction="Heart Issue Detected",
        raw=1,
        confidence=85.0,
        risk_level="High"
    )

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    mock_generate.return_value = (
        f"[BOOKING_ACTION: doctor_id={doctor.id}, date={tomorrow}, time=14:30, reason=consultation]"
    )

    result = await agent.chat("Book appointment", [])

    assert result["action_triggered"] is True
    assert result["booking_details"] is not None

    # Verify that the pre-screening brief is prepended to the appointment reason
    appt = db_session.query(models.Appointment).filter(models.Appointment.id == result["booking_details"]["id"]).first()
    assert appt is not None
    assert "[AI Risk Screen: Heart High Risk (85.0%)]" in appt.reason
    assert "consultation" in appt.reason

# --- API Integration Tests ---

def test_api_agent_chat_endpoint(client, db_session):
    """Test the POST /appointments/agent-chat REST endpoint."""
    run_id = str(uuid.uuid4())[:8]

    # Register/Login
    username = f"user_{run_id}"
    password = "TestUser123!"
    payload = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "full_name": "Test User",
        "dob": "1990-01-01"
    }
    client.post("/signup", json=payload)
    token_res = client.post("/token", data={"username": username, "password": password})
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query endpoint
    chat_payload = {
        "message": "Hello, I want to book a doctor",
        "history": [{"role": "user", "content": "Hi"}]
    }

    with patch("backend.core_ai.generate", AsyncMock(return_value="Hello! Which doctor or specialty are you looking for?")):
        res = client.post("/appointments/agent-chat", json=chat_payload, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert "action_triggered" in data

def test_api_agent_stream_endpoint(client, db_session):
    """Test the POST /appointments/agent-stream SSE endpoint."""
    run_id = str(uuid.uuid4())[:8]

    # Register/Login
    username = f"user_{run_id}"
    password = "TestUser123!"
    payload = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "full_name": "Test User",
        "dob": "1990-01-01"
    }
    client.post("/signup", json=payload)
    token_res = client.post("/token", data={"username": username, "password": password})
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query endpoint
    chat_payload = {
        "message": "Hello, I want to book a doctor",
        "history": [{"role": "user", "content": "Hi"}]
    }

    async def mock_stream(*args, **kwargs):
        yield "Sure! "
        yield "Let's check. "
        yield "Done."

    with patch("backend.core_ai.chat_stream", mock_stream):
        res = client.post("/appointments/agent-stream", json=chat_payload, headers=headers)

    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    # Read some stream lines
    lines = []
    for line in res.iter_lines():
        if isinstance(line, bytes):
            lines.append(line.decode("utf-8"))
        else:
            lines.append(line)

    non_empty = [line for line in lines if line.strip()]
    assert len(non_empty) > 0
    assert any("Sure!" in line for line in non_empty)

@pytest.mark.asyncio
@patch("backend.core_ai.generate")
async def test_agent_prefetch_and_rag_injection(mock_generate, db_session, test_users, mock_rag_by_default):
    """Test that agent pre-fetches patient history, serializes to FHIR, indexes it, and retrieves it via RAG."""
    mock_get_store, mock_search = mock_rag_by_default
    mock_store_instance = mock_get_store.return_value

    patient = test_users["patient"]
    doctor = test_users["doctor"]
    agent = SchedulingAgent(db_session, patient)

    # Add active ABDM consent to allow pre-fetching
    consent = models.InteroperabilityConsent(
        facility_id=patient.facility_id,
        patient_id=patient.id,
        status="active"
    )
    db_session.add(consent)
    db_session.commit()

    # 1. Create past clinical records in the database
    # Encounter
    encounter = models.Encounter(
        patient_id=patient.id,
        doctor_id=doctor.id,
        status="closed",
        encounter_type="AMB",
        started_at=datetime.now() - timedelta(days=2),
        ended_at=datetime.now() - timedelta(days=2, hours=23)
    )
    db_session.add(encounter)

    # VitalObservation
    obs = models.VitalObservation(
        patient_id=patient.id,
        heart_rate=72.0,
        systolic_bp=120.0,
        diastolic_bp=80.0,
        spo2=99.0,
        observed_at=datetime.now() - timedelta(days=2)
    )
    db_session.add(obs)

    # Prescription
    prescription = models.Prescription(
        patient_id=patient.id,
        doctor_id=doctor.id,
        status="active",
        created_at=datetime.now() - timedelta(days=2)
    )
    db_session.add(prescription)
    db_session.commit()
    db_session.refresh(prescription)

    # Prescription Item
    item = models.PrescriptionItem(
        prescription_id=prescription.id,
        medication_name="Aspirin",
        dosage="81mg",
        frequency="daily",
        duration="30 days",
        instructions="Take with water"
    )
    db_session.add(item)

    # CareEvent
    event = models.CareEvent(
        patient_id=patient.id,
        event_type="checkup",
        title="Post-discharge follow up",
        severity="routine",
        created_at=datetime.now() - timedelta(days=2)
    )
    db_session.add(event)

    # Invoice
    invoice = models.Invoice(
        patient_id=patient.id,
        status="paid",
        total_amount=1500.00,
        currency="INR",
        issued_at=datetime.now() - timedelta(days=2)
    )
    db_session.add(invoice)
    db_session.commit()

    # Mock RAG search to return a sample summary snippet
    mock_search.return_value = [
        "Resource: Observation/1\nVitals:\n- Heart rate: 72.0 beats/minute\n- Systolic blood pressure: 120.0 mmHg"
    ]

    # Call get_system_prompt
    prompt = agent.get_system_prompt()

    # Assert RAG add was called with patient-scoped metadata
    mock_store_instance.add.assert_called_once()
    args, kwargs = mock_store_instance.add.call_args
    # First arg is text_summary
    assert "Patient ID:" in args[0]
    assert "Aspirin" in args[0]
    assert "Post-discharge follow up" in args[0]
    assert "1500" in args[0]
    # Second arg is metadata
    assert args[1]["user_id"] == str(patient.id)
    assert args[1]["type"] == "fhir_bundle_summary"

    # Assert search_similar_records was called with correct filter query and user ID
    mock_search.assert_called_once_with(
        user_id=str(patient.id),
        query="FHIR Bundle Patient History Summary",
        n_results=3,
        facility_id=str(patient.facility_id)
    )

    # Assert prompt contains the history retrieved from RAG
    assert "Patient Historical Clinical Summary (FHIR-aligned):" in prompt
    assert "Heart rate: 72.0 beats/minute" in prompt
