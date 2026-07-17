import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from backend.models.auth import User

@pytest.mark.anyio
@patch("backend.core_ai.chat")
async def test_langgraph_low_urgency_flow(mock_chat):
    # Call 1: Triage Node (LOW)
    # Call 2: Compliance Node
    mock_chat.side_effect = [
        "Patient presents with mild cough. Recommendation: Rest. Urgency: LOW.",
        "Clinical verification clear. Disclaimer: AI-generated health advice."
    ]

    from backend.langgraph_orchestrator import run_langgraph_triage
    report = await run_langgraph_triage("Patient has mild cough.")

    assert report["urgency_level"] == "LOW"
    assert report["safety_approved"] is True
    assert len(report["steps"]) == 2
    assert report["steps"][0]["node"] == "TriageAgent"
    assert report["steps"][1]["node"] == "ComplianceAgent"
    assert "mild cough" in report["steps"][0]["text"]
    assert "Disclaimer" in report["steps"][1]["text"]

@pytest.mark.anyio
@patch("backend.core_ai.chat")
async def test_langgraph_high_urgency_flow(mock_chat):
    # Call 1: Triage Node (HIGH)
    # Call 2: Escalation Node
    # Call 3: Compliance Node
    mock_chat.side_effect = [
        "Patient presents with severe chest pain. Flag: HIGH URGENCY.",
        "Initiate emergency cardiac protocols immediately.",
        "Clinical verification clear. Disclaimer: AI-generated health advice."
    ]

    from backend.langgraph_orchestrator import run_langgraph_triage
    report = await run_langgraph_triage("Patient has severe chest pain.")

    assert report["urgency_level"] == "HIGH"
    assert report["safety_approved"] is True
    assert len(report["steps"]) == 3
    assert report["steps"][0]["node"] == "TriageAgent"
    assert report["steps"][1]["node"] == "EscalationAgent"
    assert report["steps"][2]["node"] == "ComplianceAgent"
    assert "cardiac protocols" in report["steps"][1]["text"]

def test_langgraph_triage_endpoint_unauthorized(client):
    resp = client.post("/v1/admin/agents/langgraph-triage?symptoms=cough")
    assert resp.status_code == 401

@patch("backend.core_ai.chat")
def test_langgraph_triage_endpoint_authorized(mock_chat, client, db_session: Session):
    mock_chat.side_effect = [
        "Patient has standard symptoms. Urgency: LOW.",
        "Disclaimer: AI-generated health advice."
    ]

    # Create admin
    from backend.auth import get_password_hash
    admin_user = User(
        username="langgraph_admin",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        email="langgraph_admin@example.com"
    )
    db_session.add(admin_user)
    db_session.commit()

    auth_resp = client.post(
        "/v1/token",
        data={"username": "langgraph_admin", "password": "adminpass"}
    )
    assert auth_resp.status_code == 200
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/v1/admin/agents/langgraph-triage?symptoms=Cough+and+runny+nose.&patient_id=1",
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["urgency_level"] == "LOW"
    assert data["safety_approved"] is True
    assert len(data["steps"]) == 2
