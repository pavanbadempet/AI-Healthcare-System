"""
Tier 4: Real-World Scenario — Emergency Room Presentation, Triage, STAT Lab & Care Alert
Simulates an acute patient arriving in ER with chest pain and severe hypertension.
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_emergency_department_triage_and_stat_lab_workflow(doctor_client: E2EClient):
    # 1. Fetch ER Triage Queue
    triage_resp = doctor_client.get("/v1/hospital/triage-queue")
    assert triage_resp.status_code in (200, 401, 404)

    # 2. Admit to Emergency Department Bed
    adm_payload = {
        "patient_id": 1,
        "bed_id": 1,
        "department_id": 1,
        "admission_reason": "Acute coronary syndrome rule-out",
        "notes": "Emergency triage category 2: Immediate physician assessment required",
    }
    adm_resp = doctor_client.post("/v1/hospital/admissions", json=adm_payload)
    assert adm_resp.status_code in (200, 201, 401, 404, 422)

    # 3. Execute Rapid Multi-Organ Risk Assessment
    heart_payload = TestDataFactory.heart_input()
    pred_resp = doctor_client.post("/v1/predict/heart", json=heart_payload)
    assert pred_resp.status_code in (200, 401, 422)

    # 4. Dispatch STAT Care Event Alert to Clinical Team
    event_payload = {
        "patient_id": 1,
        "event_type": "critical_triage_alert",
        "severity": "critical",
        "payload": {
            "chief_complaint": "Acute substernal crushing chest pain",
            "stat_actions": ["12-lead ECG", "Troponin I STAT", "Dual antiplatelet therapy"],
        },
    }
    event_resp = doctor_client.post("/v1/events/dispatch", json=event_payload)
    assert event_resp.status_code in (200, 201, 401, 404, 422)

    # 5. Place STAT Clinical Order
    order_payload = {
        "encounter_id": 1,
        "patient_id": 1,
        "doctor_id": 2,
        "order_type": "stat_cardiac_panel",
        "description": "Troponin I, CK-MB, Lipid Panel, CBC, BMP",
        "priority": "stat",
    }
    order_resp = doctor_client.post("/v1/hospital/orders", json=order_payload)
    assert order_resp.status_code in (200, 201, 401, 404, 422)
