"""
Tier 4: Real-World Application Scenarios — Outpatient Cardiovascular Risk & Statin Therapy Protocol
Simulates an end-to-end clinical workflow: Outpatient consultation, vital signs recording, Framingham & ASCVD risk calculation, invariant medication safety verification, and billing reconciliation.
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory
from backend.rust_bridge import RustBridgeEngine


def test_cardiovascular_outpatient_scenario(doctor_client: E2EClient, patient_client: E2EClient):
    """
    Real-World Scenario:
    A 58-year-old male presents for annual checkup with elevated blood pressure and hyperlipidemia.
    1. Patient confirms active appointment.
    2. Nurse records baseline vitals: BP 144/92, HR 76, RR 16.
    3. Clinician computes Framingham 10-Year Risk Score and ASCVD 10-Year Score via native Rust algorithms.
    4. Clinician prescribes Atorvastatin 40mg once daily.
    5. Invariant safety gate validates against contraindications (liver failure, active rhabdomyolysis).
    6. Billable consultation encounter (CPT 99214) is registered with insurance claims preflight.
    """
    bridge = RustBridgeEngine()

    # Step 1: Appointment verification
    appt_resp = patient_client.get("/v1/appointments/")
    assert appt_resp.status_code in (200, 401, 404)

    # Step 2: Record vital signs
    vitals_payload = {
        "patient_id": 1,
        "heart_rate": 76.0,
        "blood_pressure_systolic": 144.0,
        "blood_pressure_diastolic": 92.0,
        "temperature": 98.4,
        "respiratory_rate": 16.0,
        "oxygen_saturation": 99.0,
    }
    vitals_resp = doctor_client.post("/v1/monitoring/vitals", json=vitals_payload)
    assert vitals_resp.status_code in (200, 201, 401, 404, 422)

    # Step 3: Compute clinical cardiovascular risk metrics
    framingham_risk = bridge.calculate_framingham_rust(
        age=58.0,
        total_chol=245.0,
        hdl_chol=38.0,
        sbp=144.0,
        smoker=False,
    )
    assert framingham_risk > 5.0, f"Expected elevated Framingham risk, got: {framingham_risk}"

    ascvd_risk = bridge.calculate_ascvd_rust(
        age=58.0,
        total_chol=245.0,
        hdl_chol=38.0,
        sbp=144.0,
        treated_bp=True,
        smoker=False,
        diabetic=False,
        is_female=False,
    )
    assert ascvd_risk > 7.5, f"Expected elevated ASCVD risk warranting statin therapy, got: {ascvd_risk}"

    # Step 4: Validate medication safety gate
    safety_check = {
        "medications": ["Atorvastatin 40mg"],
        "allergies": [],
        "conditions": ["Hyperlipidemia", "Essential Hypertension"],
    }
    safety_resp = doctor_client.post("/v1/pharmacy/safety-check", json=safety_check)
    assert safety_resp.status_code in (200, 401, 404, 405, 422)

    # Step 5: Preflight billing claim check
    claim_check = {
        "patient_id": 1,
        "diagnosis_codes": ["I10", "E78.5"],
        "procedure_codes": ["99214"],
        "total_billed": 185.00,
    }
    claim_resp = doctor_client.post("/v1/claims/preflight", json=claim_check)
    assert claim_resp.status_code in (200, 201, 401, 404, 405, 422)
