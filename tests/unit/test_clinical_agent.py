import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.agents.base_agent import BaseAgent
from backend.agents.clinical_audit_agent import ClinicalAuditAgent
from backend.database import Base
from backend.models.auth import User
from backend.models.clinical import MonitoringSignal, VitalObservation


# Setup in-memory SQLite database for testing
@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_base_agent_telemetry():
    """Verify BaseAgent lifecycle, step logging, and token estimation."""
    agent = BaseAgent(name="Test Base Agent")
    assert agent.status == "initialized"
    assert len(agent.steps) == 0

    agent.start()
    assert agent.status == "running"
    assert len(agent.steps) == 1
    assert agent.steps[0]["action"] == "Initialize Agent"

    # Log step
    agent.log_step("Test Action", "Result summary")
    assert len(agent.steps) == 2
    assert agent.steps[1]["action"] == "Test Action"

    # Token estimation
    agent.estimate_tokens("Hello world", is_output=False)  # 11 chars -> ~2 tokens
    agent.estimate_tokens("Response text content", is_output=True)  # 21 chars -> ~5 tokens
    assert agent.input_tokens_estimated == 2
    assert agent.output_tokens_estimated == 5
    assert agent.estimated_cost > 0.0

    # Error logging
    agent.log_error("Simulated failure")
    assert len(agent.errors) == 1
    assert agent.steps[-1]["action"] == "Error Encountered"

    agent.finish()
    assert agent.status == "completed"
    assert agent.steps[-1]["action"] == "Shutdown Agent"
    assert agent.duration >= 0.0


def test_base_agent_github_actions():
    """Verify BaseAgent integration with GHA file outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        summary_file = os.path.join(tmpdir, "summary.md")
        output_file = os.path.join(tmpdir, "outputs.txt")

        # Mock GHA environments
        custom_env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_STEP_SUMMARY": summary_file,
            "GITHUB_OUTPUT": output_file,
        }

        with patch.dict(os.environ, custom_env):
            agent = BaseAgent("GHA Agent")
            agent.start()
            agent.estimate_tokens("Input", is_output=False)
            agent.estimate_tokens("Output", is_output=True)
            agent.finish()

            # Verify step summary written
            assert os.path.exists(summary_file)
            with open(summary_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "# ✅ APEX Agent Execution Summary: GHA Agent" in content
                assert "Est. Input Tokens" in content

            # Verify outputs written
            assert os.path.exists(output_file)
            with open(output_file, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
                assert "agent_status=completed" in lines
                assert "input_tokens=1" in lines
                assert "output_tokens=1" in lines


@pytest.mark.asyncio
async def test_clinical_audit_agent_no_data(db_session):
    """Verify ClinicalAuditAgent behavior on empty database."""
    agent = ClinicalAuditAgent(db_session, "Empty DB Auditor")
    report, report_json = await agent.run(hours=24, dry_run=True)

    assert "No high-risk patients or critical alerts found" in report
    assert agent.status == "completed"
    assert len(agent.steps) == 5  # Init, Fetch, Filter, Skip, Shutdown
    assert report_json["status"] == "completed"
    assert report_json["audited_patients_count"] == 0


@pytest.mark.asyncio
async def test_clinical_audit_agent_with_data(db_session):
    """Verify ClinicalAuditAgent processes alerts and builds clinical report."""
    # Seed mock patient
    patient = User(
        id=101,
        username="patient101",
        email="patient101@test.com",
        full_name="Jane Doe",
        role="patient",
    )
    db_session.add(patient)
    db_session.commit()

    # Seed mock critical vitals
    vital = VitalObservation(
        patient_id=101,
        heart_rate=125.0,
        systolic_bp=145.0,
        diastolic_bp=95.0,
        spo2=88.0,
        temperature_c=38.5,
        respiratory_rate=24.0,
        observed_at=datetime.now(timezone.utc),
    )
    db_session.add(vital)
    db_session.commit()

    # Seed mock critical signal
    signal = MonitoringSignal(
        patient_id=101,
        vital_observation_id=vital.id,
        signal_type="hypoxia",
        severity="critical",
        title="Critical Hypoxia Detected",
        summary="SpO2 at 88% which is below safe threshold.",
        status="open",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(signal)
    db_session.commit()

    # Run agent in dry run mode (uses local mockup assessment)
    agent = ClinicalAuditAgent(db_session, "Active DB Auditor")
    report, report_json = await agent.run(hours=24, dry_run=True)

    assert "Jane Doe" in report
    assert "88.0%" in report
    assert "Critical Hypoxia" in report
    assert "[HEURISTIC LOCAL ASSESSMENT" in report
    assert agent.status == "completed"
    assert agent.input_tokens_estimated > 0
    assert agent.output_tokens_estimated > 0
    assert report_json["audited_patients_count"] == 1
    assert report_json["audits"][0]["patient_name"] == "Jane Doe"
