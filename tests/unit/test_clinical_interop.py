
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.hl7_receiver import process_hl7_message
from backend.models.auth import User
from backend.models.clinical import VitalObservation
from backend.questionnaire import ingest_fhir_questionnaire_response
from backend.terminology import semantic_map_symptoms

# ── DB fixture ────────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    """Isolated in-memory SQLite database setup for interoperability tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

# ── Concept Mapper Tests ──────────────────────────────────────────────────────

def test_terminology_concept_auto_mapper():
    # 1. Test query mapping for heart rate synonym
    matches = semantic_map_symptoms("Patient has an elevated pulse.")
    assert len(matches) > 0
    displays = [m["display"] for m in matches]
    assert any("Heart rate" in d for d in displays)

    # 2. Test query mapping for blood glucose
    matches = semantic_map_symptoms("Blood sugar levels look slightly high.")
    assert len(matches) > 0
    displays = [m["display"] for m in matches]
    assert any("Glucose" in d or "Diabetes" in d for d in displays)

    # 3. Test query mapping for asthma
    matches = semantic_map_symptoms("Asthma symptom checkup")
    assert len(matches) > 0
    displays = [m["display"] for m in matches]
    assert "Asthma" in displays

    # 4. Test empty query
    assert semantic_map_symptoms("") == []

# ── HL7 v2 Message Ingestion Tests ───────────────────────────────────────────

def test_hl7_patient_update_parsing(db):
    # HL7 ADT^A08 Message: Update Patient Profile
    hl7_msg = (
        "MSH|^~\\&|EPIC|OAKWOOD|||20260716180000||ADT^A08|MSG00001|P|2.3\r"
        "PID|||101||Doe^Jane||19850520|F|||123 Maple St||jane.doe@example.com\r"
        "PV1||O|OP^Outpatient||||||||||||||||||||||||||||||||||||||||||20260716180000"
    )

    res = process_hl7_message(hl7_msg, db)
    assert res["status"] == "success"
    assert "ADT" in res["message_type"]
    assert res["patient_name"] == "Jane Doe"

    # Query DB to verify patient profile was created/synchronized
    patient = db.query(User).filter(User.id == res["patient_id"]).first()
    assert patient is not None
    assert patient.full_name == "Jane Doe"
    assert patient.dob == "1985-05-20"
    assert patient.gender == "female"
    assert patient.email == "jane.doe@example.com"

def test_hl7_vital_observation_parsing(db):
    # Register/create the patient profile in the DB first
    patient = User(id=102, username="hl7_102", hashed_password="pw", role="patient")
    db.add(patient)
    db.commit()

    # HL7 ORU^R01 Message: Ingest vital signs (Heart rate, blood glucose, temperature)
    hl7_msg = (
        "MSH|^~\\&|CARDIOLOGY_MONITOR||||20260716180000||ORU^R01|MSG00002|P|2.3\r"
        "PID|||102||Doe^John\r"
        "OBX|1|NM|8867-4^Heart rate^LN||78.5|/min|||||F|||20260716180000\r"
        "OBX|2|NM|2339-0^Glucose^LN||120.0|mg/dL|||||F|||20260716180000\r"
        "OBX|3|NM|8310-5^Body temperature^LN||37.2|C|||||F|||20260716180000"
    )

    res = process_hl7_message(hl7_msg, db)
    assert res["status"] == "success"
    assert "ORU" in res["message_type"]
    assert res["records_created"] == 1

    # Verify vital observation was inserted in DB
    obs = db.query(VitalObservation).filter(VitalObservation.patient_id == res["patient_id"]).first()
    assert obs is not None
    assert obs.heart_rate == 78.5
    assert obs.blood_glucose == 120.0
    assert obs.temperature_c == 37.2
    assert obs.source == "device"

# ── FHIR Questionnaire Ingestion Tests ────────────────────────────────────────

def test_fhir_questionnaire_response_ingestion(db):
    # FHIR Questionnaire defining vital questions
    questionnaire = {
        "resourceType": "Questionnaire",
        "id": "vitals-intake-form",
        "status": "active",
        "item": [
            {
                "linkId": "q-heart-rate",
                "text": "What is your heart rate?",
                "type": "decimal",
                "code": [{"system": "http://loinc.org", "code": "8867-4"}]
            },
            {
                "linkId": "q-blood-glucose",
                "text": "What is your glucose level?",
                "type": "decimal",
                "code": [{"system": "http://loinc.org", "code": "2339-0"}]
            }
        ]
    }

    # FHIR QuestionnaireResponse submitted by a patient
    # Note: Patient/103 reference will create user id 103 in the DB
    response = {
        "resourceType": "QuestionnaireResponse",
        "questionnaire": "Questionnaire/vitals-intake-form",
        "status": "completed",
        "authored": "2026-07-16T18:00:00Z",
        "subject": {
            "reference": "Patient/103"
        },
        "item": [
            {
                "linkId": "q-heart-rate",
                "answer": [{"valueDecimal": 72.0}]
            },
            {
                "linkId": "q-blood-glucose",
                "answer": [{"valueInteger": 105}]
            }
        ]
    }

    res = ingest_fhir_questionnaire_response(response, questionnaire, db)
    assert res["status"] == "success"
    assert res["records_created"] == 1
    assert "heart_rate" in res["vitals_mapped"]
    assert "blood_glucose" in res["vitals_mapped"]

    # Verify recorded database observation
    obs = db.query(VitalObservation).filter(VitalObservation.patient_id == res["patient_id"]).first()
    assert obs is not None
    assert obs.heart_rate == 72.0
    assert obs.blood_glucose == 105.0
    assert obs.source == "patient_reported"
