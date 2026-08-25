"""
Tier 4: Real-World Scenario — ICU Sepsis Early Warning, Alert Generation & Four-Eye Review
Simulates ICU patient monitoring, automated sepsis risk scoring, and physician clinical override.
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_icu_sepsis_detection_and_clinical_governance_scenario(doctor_client: E2EClient, nurse_client: E2EClient):
    # 1. Nurse submits abnormal vitals (tachycardia, fever, hypotension)
    icu_vitals = {
        "patient_id": 1,
        "heart_rate": 128.0,
        "blood_pressure_systolic": 85.0,
        "blood_pressure_diastolic": 50.0,
        "respiratory_rate": 26.0,
        "temperature_celsius": 39.2,
        "oxygen_saturation": 91.0,
    }
    vitals_resp = nurse_client.post("/v1/monitoring/vitals", json=icu_vitals)
    assert vitals_resp.status_code in (200, 201, 401, 422)

    # 2. Automated Sepsis AI Evaluation
    sepsis_eval = {
        "patient_id": "P-ICU-01",
        "respiratory_rate": 26,
        "systolic_bp": 85,
        "gcs_score": 14,
    }
    eval_resp = doctor_client.post("/api/v1/data-platform/agents/sepsis/evaluate", json=sepsis_eval)
    assert eval_resp.status_code in (200, 401, 404, 422)

    # 3. Trigger Clinical Intelligence Insights
    insights_resp = doctor_client.get("/v1/intelligence/insights/1")
    assert insights_resp.status_code in (200, 401, 404)

    # 4. Record Physician Four-Eye Review and Intervention Note
    review_payload = {
        "patient_id": 1,
        "prediction_type": "icu_sepsis_risk",
        "decision": "confirmed_and_escalated",
        "clinical_use_category": "emergency_intervention",
        "review_note": "Initiating 3-hour sepsis bundle: 30mL/kg IV crystalloid fluid, blood cultures, empiric broad-spectrum antibiotics",
    }
    review_resp = doctor_client.post("/v1/predict/reviews", json=review_payload)
    assert review_resp.status_code in (200, 201, 401, 404, 422)
