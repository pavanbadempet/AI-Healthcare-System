import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.orm import Session

from backend.models.auth import User
from backend.models.clinical import VitalObservation
from backend.agents.billing_agent import ClinicalBillingAgent
from backend.agents.discharge_agent import ClinicalDischargeAgent
from backend.agents.nursing_agent import ClinicalNursingAgent
from backend.agents.patch_agent import ClinicalPatchAgent
from backend.agents.fixing_agent import ClinicalFixingAgent
from backend.agents.calling_agent import ClinicalCallingAgent
from backend.agents.wellness_agent import ClinicalWellnessAgent

@pytest.mark.anyio
@patch("backend.agents.billing_agent.generate")
async def test_clinical_billing_agent(mock_generate, db_session: Session):
    mock_generate.return_value = (
        '{"icd10_codes": ["I25.1", "E11.9"], '
        '"cpt_codes": ["93000", "99213"], '
        '"denial_risk": "LOW", '
        '"warnings": [], '
        '"recommendations": ["Ensure documentation of chest pain severity."]}'
    )
    
    agent = ClinicalBillingAgent(db_session)
    report = await agent.audit_billing_claim("Patient presents with chest pain and history of diabetes.")
    
    assert report["data"]["denial_risk"] == "LOW"
    assert "I25.1" in report["data"]["icd10_codes"]
    assert "93000" in report["data"]["cpt_codes"]
    assert report["telemetry"]["input_tokens"] > 0

@pytest.mark.anyio
@patch("backend.agents.discharge_agent.generate")
async def test_clinical_discharge_agent(mock_generate, db_session: Session):
    mock_generate.return_value = (
        '{"discharge_summary": "Patient discharged stable.", '
        '"transition_plan": ["Limit heavy lifting", "Low sodium diet"], '
        '"patient_instructions": "Take medication on time.", '
        '"follow_up_appointments": "Follow up with PCP in 1 week."}'
    )
    
    # Seed a patient
    patient = User(
        username="discharge_patient",
        role="patient",
        dob="1980-05-15",
        gender="1",
        existing_ailments="Hypertension"
    )
    db_session.add(patient)
    db_session.commit()
    
    agent = ClinicalDischargeAgent(db_session)
    report = await agent.generate_discharge_plan(patient.id)
    
    assert report["data"]["discharge_summary"] == "Patient discharged stable."
    assert "Limit heavy lifting" in report["data"]["transition_plan"]
    assert report["data"]["follow_up_appointments"] == "Follow up with PCP in 1 week."

@pytest.mark.anyio
@patch("backend.agents.nursing_agent.generate")
async def test_clinical_nursing_agent(mock_generate, db_session: Session):
    mock_generate.return_value = (
        '{"handoff_summary": "Stable overnight.", '
        '"priority_tasks": ["Check blood sugar", "Assess pain"], '
        '"monitoring_frequency": "Q4h", '
        '"safety_concerns": ["Fall risk"]}'
    )
    
    # Seed a patient and vitals
    patient = User(username="nursing_patient", role="patient")
    db_session.add(patient)
    db_session.commit()
    
    vital = VitalObservation(
        patient_id=patient.id,
        heart_rate=72,
        systolic_bp=120,
        diastolic_bp=80,
        temperature_c=36.8
    )
    db_session.add(vital)
    db_session.commit()
    
    agent = ClinicalNursingAgent(db_session)
    report = await agent.generate_handoff_card(patient.id)
    
    assert report["data"]["handoff_summary"] == "Stable overnight."
    assert "Check blood sugar" in report["data"]["priority_tasks"]
    assert report["data"]["monitoring_frequency"] == "Q4h"

def test_admin_agent_endpoints_unauthorized(client):
    # Billing
    resp = client.post("/v1/admin/agents/billing-audit?soap_note=test")
    assert resp.status_code == 401
    
    # Discharge
    resp = client.post("/v1/admin/agents/discharge-summary?patient_id=1")
    assert resp.status_code == 401
    
    # Nursing
    resp = client.post("/v1/admin/agents/nursing-handoff?patient_id=1")
    assert resp.status_code == 401

    # Security patch
    resp = client.post("/v1/admin/agents/security-patch?dependencies=test")
    assert resp.status_code == 401

    # Auto fix
    resp = client.post("/v1/admin/agents/auto-fix?error_logs=test")
    assert resp.status_code == 401

    # Auto call
    resp = client.post("/v1/admin/agents/auto-call?alert_details=test")
    assert resp.status_code == 401

    # Wellness advisory
    resp = client.post("/v1/admin/agents/wellness-advisory?patient_data=test")
    assert resp.status_code == 401

@patch("backend.agents.wellness_agent.generate")
@patch("backend.agents.calling_agent.generate")
@patch("backend.agents.fixing_agent.generate")
@patch("backend.agents.patch_agent.generate")
@patch("backend.agents.nursing_agent.generate")
@patch("backend.agents.discharge_agent.generate")
@patch("backend.agents.billing_agent.generate")
def test_admin_agent_endpoints_authorized(mock_billing, mock_discharge, mock_nursing, mock_patch, mock_fix, mock_call, mock_well, client, db_session: Session):
    mock_billing.return_value = '{"icd10_codes": [], "cpt_codes": [], "denial_risk": "LOW", "warnings": [], "recommendations": []}'
    mock_discharge.return_value = '{"discharge_summary": "Discharged", "transition_plan": [], "patient_instructions": "", "follow_up_appointments": ""}'
    mock_nursing.return_value = '{"handoff_summary": "Handoff", "priority_tasks": [], "monitoring_frequency": "", "safety_concerns": []}'
    mock_patch.return_value = '{"vulnerabilities": [], "posture_score": 95, "recommended_patches": [], "hotpatches_applied": []}'
    mock_fix.return_value = '{"faults_detected": [], "healing_actions": [], "status": "restored"}'
    mock_call.return_value = '{"urgency": "CRITICAL", "assigned_contact": "Dr. Sarah", "call_script": "Alert", "broadcast_success": true}'
    mock_well.return_value = '{"wellness_plan": [], "disclaimer": "Advice", "symptom_urgency": "low"}'
    
    # Create admin
    from backend.auth import get_password_hash
    admin_user = User(
        username="agent_admin",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        email="agent_admin@example.com"
    )
    db_session.add(admin_user)
    
    # Create patient for endpoints
    patient = User(username="endpoint_patient", role="patient")
    db_session.add(patient)
    db_session.commit()
    
    # Capture patient ID locally to avoid DetachedInstanceError
    patient_id = patient.id
    
    auth_resp = client.post(
        "/v1/token",
        data={"username": "agent_admin", "password": "adminpass"}
    )
    assert auth_resp.status_code == 200
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Billing audit
    resp = client.post(
        "/v1/admin/agents/billing-audit?soap_note=Patient+presents+with+fever.",
        headers=headers
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    
    # 2. Discharge summary
    resp = client.post(
        f"/v1/admin/agents/discharge-summary?patient_id={patient_id}",
        headers=headers
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    
    # 3. Nursing handoff
    resp = client.post(
        f"/v1/admin/agents/nursing-handoff?patient_id={patient_id}",
        headers=headers
    )
    assert resp.status_code == 200
    assert "data" in resp.json()

    # 4. Security patch
    resp = client.post(
        "/v1/admin/agents/security-patch?dependencies=FastAPI",
        headers=headers
    )
    assert resp.status_code == 200
    assert "report" in resp.json()

    # 5. Auto fix
    resp = client.post(
        "/v1/admin/agents/auto-fix?error_logs=OperationalError",
        headers=headers
    )
    assert resp.status_code == 200
    assert "report" in resp.json()

    # 6. Auto call
    resp = client.post(
        "/v1/admin/agents/auto-call?alert_details=Cardiac",
        headers=headers
    )
    assert resp.status_code == 200
    assert "report" in resp.json()

    # 7. Wellness advisory
    resp = client.post(
        "/v1/admin/agents/wellness-advisory?patient_data=Symptom",
        headers=headers
    )
    assert resp.status_code == 200
    assert "report" in resp.json()


@patch("backend.agents.nursing_agent.generate")
@patch("backend.agents.discharge_agent.generate")
@patch("backend.agents.billing_agent.generate")
def test_sota_agents_domain_routes(mock_billing, mock_discharge, mock_nursing, client, db_session: Session):
    mock_billing.return_value = '{"icd10_codes": [], "cpt_codes": [], "denial_risk": "LOW", "warnings": [], "recommendations": []}'
    mock_discharge.return_value = '{"discharge_summary": "Discharged", "transition_plan": [], "patient_instructions": "", "follow_up_appointments": ""}'
    mock_nursing.return_value = '{"handoff_summary": "Handoff", "priority_tasks": [], "monitoring_frequency": "", "safety_concerns": []}'
    
    # Create admin user
    from backend.auth import get_password_hash
    admin_user = User(
        username="domain_admin",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        email="domain_admin@example.com"
    )
    db_session.add(admin_user)
    
    # Create patient
    patient = User(username="domain_patient", role="patient")
    db_session.add(patient)
    db_session.commit()
    
    patient_id = patient.id
    
    # Create invoice for billing audit
    from backend.models.billing import Invoice
    invoice = Invoice(
        patient_id=patient_id,
        facility_id=1,
        status="issued",
        subtotal=100.0,
        discount_amount=0.0,
        tax_amount=0.0,
        total_amount=100.0
    )
    db_session.add(invoice)
    db_session.commit()
    invoice_id = invoice.id
    
    # Generate token
    auth_resp = client.post(
        "/v1/token",
        data={"username": "domain_admin", "password": "adminpass"}
    )
    assert auth_resp.status_code == 200
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Billing invoice audit
    resp = client.post(
        f"/v1/billing/invoices/{invoice_id}/audit",
        headers=headers
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    
    # 2. Discharge summary generation
    resp = client.post(
        f"/v1/discharge/summaries/generate/{patient_id}",
        headers=headers
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    
    # 3. Nursing handoff generation
    resp = client.post(
        f"/v1/nursing/patients/{patient_id}/handoff",
        headers=headers
    )
    assert resp.status_code == 200
    assert "data" in resp.json()


@pytest.mark.anyio
@patch("backend.agents.patch_agent.generate")
async def test_clinical_patch_agent(mock_generate, db_session: Session):
    mock_generate.return_value = (
        '{"vulnerabilities": ["Outdated jose library"], '
        '"posture_score": 80, '
        '"recommended_patches": ["Upgrade python-jose to 3.3.0"], '
        '"hotpatches_applied": ["Applied jose JWT signature validation fix"]}'
    )
    
    agent = ClinicalPatchAgent(db_session)
    report = await agent.audit_and_apply_patches("jose==3.2.0", "SECRET_KEY: Set")
    
    assert report["status"] == "completed"
    assert report["report"]["posture_score"] == 80
    assert "Outdated jose library" in report["report"]["vulnerabilities"]
    assert "Upgrade python-jose to 3.3.0" in report["report"]["recommended_patches"]
    assert "programmatic_audit" in report["report"]
    assert "packages_scanned" in report["report"]["programmatic_audit"]
    assert "status" in report["report"]["programmatic_audit"]



@pytest.mark.anyio
@patch("backend.agents.fixing_agent.generate")
async def test_clinical_fixing_agent(mock_generate, db_session: Session):
    mock_generate.return_value = (
        '{"faults_detected": ["database is locked"], '
        '"healing_actions": ["Run VACUUM optimization", "Clear thread locks"], '
        '"status": "restored"}'
    )
    
    agent = ClinicalFixingAgent(db_session)
    report = await agent.diagnose_and_heal("OperationalError: database is locked", "CPU: 12%")
    
    assert report["status"] == "completed"
    assert report["report"]["status"] == "restored"
    assert "database is locked" in report["report"]["faults_detected"]
    assert "Run VACUUM optimization" in report["report"]["healing_actions"]
    assert report["report"]["executed_maintenance"] is True
    assert report["report"]["maintenance_report"]["status"] == "success"



@pytest.mark.anyio
@patch("backend.agents.calling_agent.generate")
async def test_clinical_calling_agent(mock_generate, db_session: Session):
    mock_generate.return_value = (
        '{"urgency": "CRITICAL", '
        '"assigned_contact": "Dr. Sarah Jenkins", '
        '"call_script": "This is an automated alert.", '
        '"broadcast_success": true}'
    )
    
    agent = ClinicalCallingAgent(db_session)
    report = await agent.route_emergency_call("Alarm: SYS_ALARM_TACHY", "Dr. Sarah Jenkins")
    
    assert report["status"] == "completed"
    assert report["report"]["urgency"] == "CRITICAL"
    assert report["report"]["assigned_contact"] == "Dr. Sarah Jenkins"
    assert report["report"]["broadcast_success"] is True
    assert "synthesized_audio_base64" in report["report"]



@pytest.mark.anyio
@patch("backend.agents.wellness_agent.generate")
async def test_clinical_wellness_agent(mock_generate, db_session: Session):
    mock_generate.return_value = (
        '{"wellness_plan": ["Incorporate leafy greens", "Walk 30 mins daily"], '
        '"disclaimer": "Medical Disclaimer: Consult clinical experts.", '
        '"symptom_urgency": "low"}'
    )
    
    agent = ClinicalWellnessAgent(db_session)
    report = await agent.generate_wellness_plan("Sedentary lifestyle and fatigue")
    
    assert report["status"] == "completed"
    assert report["report"]["symptom_urgency"] == "low"
    assert "Medical Disclaimer: Consult clinical experts." in report["report"]["disclaimer"]
    assert "Incorporate leafy greens" in report["report"]["wellness_plan"]

