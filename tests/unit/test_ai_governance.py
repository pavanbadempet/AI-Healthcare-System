import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend import ai_governance
from backend import models

# In-memory database for testing
@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_registry_contains_core_clinical_functions():
    functions = ai_governance.get_registered_functions()
    assert len(functions) >= 5
    names = {f["name"] for f in functions}
    assert "heart_risk_prediction" in names
    assert "diabetes_risk_prediction" in names
    assert "ambient_scribe_soap" in names

def test_clinician_override_logging_and_report(db_session):
    # Setup test patients and clinicians
    patient = models.User(
        email="patient@clin.os",
        hashed_password="...",
        role="patient",
        full_name="Alice Smith"
    )
    clinician = models.User(
        email="doctor@clin.os",
        hashed_password="...",
        role="doctor",
        full_name="Dr. House"
    )
    db_session.add(patient)
    db_session.add(clinician)
    db_session.commit()

    # Log accepted event
    ai_governance.log_clinician_override(
        db=db_session,
        patient_id=patient.id,
        clinician_id=clinician.id,
        function_name="heart_risk_prediction",
        original_ai_output="High Risk",
        corrected_output="High Risk",
        override_action="accepted"
    )

    # Log overridden event
    ai_governance.log_clinician_override(
        db=db_session,
        patient_id=patient.id,
        clinician_id=clinician.id,
        function_name="heart_risk_prediction",
        original_ai_output="High Risk",
        corrected_output="Low Risk",
        override_action="overridden",
        override_reason="Vitals stable upon second review"
    )

    report = ai_governance.get_governance_report(db_session)
    heart_report = next(r for r in report if r["function_name"] == "heart_risk_prediction")

    assert heart_report["total_reviews"] == 2
    assert heart_report["accepted_count"] == 1
    assert heart_report["overridden_count"] == 1
    assert heart_report["agreement_rate"] == 0.5
    assert heart_report["status"] == "needs_calibration"
