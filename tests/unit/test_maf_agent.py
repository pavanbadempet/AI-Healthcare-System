import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from backend.models.auth import User

@pytest.mark.anyio
@patch("backend.core_ai.chat")
async def test_maf_billing_agent_flow(mock_chat):
    mock_chat.return_value = (
        '{"icd10_codes": ["I25.1", "E11.9"], '
        '"cpt_codes": ["93000", "99213"], '
        '"denial_risk": "LOW", '
        '"warnings": [], '
        '"recommendations": ["Ensure documentation of chest pain severity."]}'
    )
    
    from backend.maf_orchestrator import run_maf_billing_audit
    report = await run_maf_billing_audit("Patient presents with chest pain and history of diabetes.")
    
    assert report["data"]["denial_risk"] == "LOW"
    assert "I25.1" in report["data"]["icd10_codes"]
    assert "93000" in report["data"]["cpt_codes"]
    assert report["telemetry"]["input_tokens"] > 0

def test_maf_admin_agent_endpoint_unauthorized(client):
    resp = client.post("/v1/admin/agents/maf-billing-audit?soap_note=test")
    assert resp.status_code == 401
    
    resp2 = client.post("/v1/admin/agents/maf-handoff-audit?soap_note=test")
    assert resp2.status_code == 401

@patch("backend.core_ai.chat")
def test_maf_admin_agent_endpoint_authorized(mock_chat, client, db_session: Session):
    mock_chat.return_value = '{"icd10_codes": [], "cpt_codes": [], "denial_risk": "LOW", "warnings": [], "recommendations": []}'
    
    # Create admin
    from backend.auth import get_password_hash
    admin_user = User(
        username="maf_admin",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        email="maf_admin@example.com"
    )
    db_session.add(admin_user)
    db_session.commit()
    
    auth_resp = client.post(
        "/v1/token",
        data={"username": "maf_admin", "password": "adminpass"}
    )
    assert auth_resp.status_code == 200
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = client.post(
        "/v1/admin/agents/maf-billing-audit?soap_note=Patient+presents+with+fever.",
        headers=headers
    )
    assert resp.status_code == 200
    assert "data" in resp.json()

@pytest.mark.anyio
@patch("backend.core_ai.chat")
async def test_maf_handoff_agent_flow(mock_chat):
    mock_chat.side_effect = [
        "Billing recommended codes: ICD-10 I25.1. Handing off to SafetyComplianceAgent.",
        "Safety validation: patient context is clear. No conflicts. AUDIT COMPLETE."
    ]
    
    from backend.maf_orchestrator import run_maf_handoff_audit
    report = await run_maf_handoff_audit("Patient presents with chest pain.")
    
    assert len(report["steps"]) == 2
    assert report["steps"][0]["agent"] == "ClinicalBillingAgent"
    assert "I25.1" in report["steps"][0]["text"]
    assert report["steps"][1]["agent"] == "SafetyComplianceAgent"
    assert "AUDIT COMPLETE" in report["steps"][1]["text"]
    assert report["telemetry"]["input_tokens"] > 0

@patch("backend.core_ai.chat")
def test_maf_handoff_endpoint_authorized(mock_chat, client, db_session: Session):
    mock_chat.side_effect = [
        "Handoff trigger. Pass to SafetyComplianceAgent.",
        "Verified. AUDIT COMPLETE."
    ]
    
    # Create admin
    from backend.auth import get_password_hash
    admin_user = User(
        username="maf_handoff_admin",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        email="maf_handoff_admin@example.com"
    )
    db_session.add(admin_user)
    db_session.commit()
    
    auth_resp = client.post(
        "/v1/token",
        data={"username": "maf_handoff_admin", "password": "adminpass"}
    )
    assert auth_resp.status_code == 200
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = client.post(
        "/v1/admin/agents/maf-handoff-audit?soap_note=Patient+presents+with+fever.",
        headers=headers
    )
    assert resp.status_code == 200
    assert "steps" in resp.json()
