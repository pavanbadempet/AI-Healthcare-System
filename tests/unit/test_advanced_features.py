from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models
from backend.agents.scheduling_agent import SchedulingAgent
from backend.database import Base

# Isolated test DB
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

class TestAdvancedClinicalFeatures:
    """Tests for Phase 6 advanced clinical features: ML Triage, ABDM prefetching, and Federated simulator."""

    @pytest.mark.asyncio
    @patch("backend.core_ai.generate")
    async def test_clinical_triage_urgency_escalation(self, mock_generate, db_session):
        # 1. Create a patient and a doctor in the facility
        patient = models.User(
            id=1,
            username="patient_triage",
            email="patient@test.com",
            role="patient",
            facility_id=1,
            dob="1970-01-01"
        )
        doctor = models.User(
            id=2,
            username="doctor_triage",
            role="doctor",
            facility_id=1,
            specialization="Cardiologist"
        )
        db_session.add(patient)
        db_session.add(doctor)
        db_session.commit()

        # 2. Add an active ABDM consent to allow pre-fetching
        consent = models.InteroperabilityConsent(
            facility_id=1,
            patient_id=patient.id,
            status="active"
        )
        db_session.add(consent)

        # 3. Add abnormal vital observations (High BP)
        vital = models.VitalObservation(
            patient_id=patient.id,
            systolic_bp=150.0, # High BP
            observed_at=datetime.utcnow()
        )
        db_session.add(vital)
        db_session.commit()

        # 4. Mock model prediction to return High Risk Cardiologist screening
        mock_pred = MagicMock()
        mock_pred.prediction = 1
        mock_pred.confidence = 92.5
        mock_pred.risk_level = "High Risk"

        with patch("backend.model_service.model_service.predict_heart", return_value=mock_pred), \
             patch("backend.model_service.model_service.is_available", return_value=True):

            # Setup CASA agent
            agent = SchedulingAgent(db_session, patient)

            # Mock the LLM to output the booking action tag
            mock_generate.return_value = f"[BOOKING_ACTION: doctor_id={doctor.id}, date=2026-07-01, time=10:00, reason=Chest pain triage]"

            history = []
            res = await agent.chat("I want to book an appointment with doctor ID 2", history)

            assert res["action_triggered"] is True
            assert res["error"] is None

            # Verify appointment prefix has urgency tag and contributing risk factors
            appt = db_session.query(models.Appointment).filter(models.Appointment.user_id == patient.id).first()
            assert appt is not None
            assert "🚨 [URGENT CLINICAL TRIAGE]" in appt.reason
            assert "Elevated Rest BP" in appt.reason

            # Verify high-priority CareEvent was logged
            event = db_session.query(models.CareEvent).filter(models.CareEvent.patient_id == patient.id).first()
            assert event is not None
            assert event.event_type == "triage_escalation"
            assert event.severity == "high"
            assert "Elevated Rest BP" in event.summary

    @pytest.mark.asyncio
    @patch("backend.core_ai.generate")
    async def test_abdm_consent_linked_prefetch(self, mock_generate, db_session):
        # 1. Create a patient and doctor
        patient = models.User(
            id=3,
            username="patient_consent",
            email="patient_c@test.com",
            role="patient",
            facility_id=1
        )
        doctor = models.User(
            id=4,
            username="doctor_consent",
            role="doctor",
            facility_id=1,
            specialization="General Physician"
        )
        db_session.add(patient)
        db_session.add(doctor)
        db_session.commit()

        agent = SchedulingAgent(db_session, patient)

        # Before consent: prefetch should be bypassed
        with patch("backend.rag.get_vector_store") as mock_vector_store:
            agent.prefetch_and_index_history()
            mock_vector_store.assert_not_called()

            # The system prompt should include request instructions
            prompt = agent.get_system_prompt()
            assert "ABDM Interoperability Consent is currently INACTIVE/MISSING" in prompt

        # Send consent authorization message
        history = []
        mock_generate.return_value = "AI: I will process that."
        await agent.chat("yes, please request consent", history)

        # Consent should now be active in DB
        consent = db_session.query(models.InteroperabilityConsent).filter(
            models.InteroperabilityConsent.patient_id == patient.id,
            models.InteroperabilityConsent.status == "active"
        ).first()
        assert consent is not None

        # After consent: prefetch should trigger vector store indexing
        with patch("backend.rag.get_vector_store") as mock_vector_store:
            mock_store_inst = MagicMock()
            mock_vector_store.return_value = mock_store_inst

            agent.prefetch_and_index_history()
            assert mock_store_inst.add.call_count == 1

    def test_federated_simulation_run(self):
        from scripts.training.run_federated_sim import run_simulation

        # Run simulation with small epochs for speed
        results = run_simulation(epochs=2, epsilon=2.0)
        assert "acc_central" in results
        assert "acc_federated" in results
        assert results["acc_central"] > 0.0
        assert results["acc_federated"] > 0.0
