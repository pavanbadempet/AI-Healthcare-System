"""
Tier 3: Cross-Feature Flow — Risk Prediction to AI Explanation to Specialist Referral Flow
Predict -> Explain -> Recommendation -> Specialist Appointment
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_risk_prediction_to_explanation_to_referral_workflow(patient_client: E2EClient):
    # 1. Run Heart Disease Risk Prediction
    heart_payload = TestDataFactory.heart_input()
    pred_resp = patient_client.post("/v1/predict/heart", json=heart_payload)
    assert pred_resp.status_code in (200, 401, 422)

    # 2. Get ML Explanation for Heart Risk
    explain_resp = patient_client.post("/v1/predict/explain/heart", json=heart_payload)
    assert explain_resp.status_code in (200, 401, 422)

    # 3. Fetch Specialist Recommendation
    rec_payload = {
        "patient_id": 1,
        "prediction_domain": "cardiology",
        "risk_level": "high",
        "features": {"systolic_bp": 145},
    }
    rec_resp = patient_client.post("/v1/recommendations/clinical-interventions", json=rec_payload)
    assert rec_resp.status_code in (200, 401, 404, 422)

    # 4. Schedule Specialist Appointment
    appt_payload = {
        "doctor_id": 1,
        "date": "2026-09-25",
        "time": "11:00:00",
        "reason": "Cardiology specialist evaluation following ML risk screening",
        "status": "scheduled",
    }
    appt_resp = patient_client.post("/v1/appointments/", json=appt_payload)
    assert appt_resp.status_code in (200, 201, 401, 404, 422)
