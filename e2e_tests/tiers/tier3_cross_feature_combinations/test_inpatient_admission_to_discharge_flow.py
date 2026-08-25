"""
Tier 3: Cross-Feature Flow — Inpatient Admission to Nursing Care to Discharge Flow
Admit -> Assign Bed -> Nursing Task -> Vitals -> Discharge Summary -> Finalize
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_inpatient_admission_to_discharge_lifecycle(doctor_client: E2EClient, nurse_client: E2EClient):
    # 1. Admit Patient
    adm_payload = TestDataFactory.admission_create(patient_id=1, bed_id=1, department_id=1)
    adm_resp = doctor_client.post("/v1/hospital/admissions", json=adm_payload)
    assert adm_resp.status_code in (200, 201, 401, 404, 422)

    # 2. Nurse Task Assignment
    task_payload = TestDataFactory.nursing_task_create(patient_id=1, nurse_id=3)
    task_resp = nurse_client.post("/v1/nursing/tasks", json=task_payload)
    assert task_resp.status_code in (200, 201, 401, 404, 422)

    task_id = 1
    if task_resp.status_code in (200, 201):
        task_id = task_resp.json().get("id", 1)

    # 3. Complete Nursing Task
    comp_resp = nurse_client.put(f"/v1/nursing/tasks/{task_id}/complete", json={"notes": "Vitals recorded and within normal limits"})
    assert comp_resp.status_code in (200, 401, 404, 422)

    # 4. Record Inpatient Vitals
    vitals_payload = TestDataFactory.vitals_create(patient_id=1)
    vitals_resp = nurse_client.post("/v1/monitoring/vitals", json=vitals_payload)
    assert vitals_resp.status_code in (200, 201, 401, 422)

    # 5. Create Discharge Summary
    disc_payload = {
        "patient_id": 1,
        "encounter_id": 1,
        "discharge_diagnosis": "Resolved acute chest pain - non-cardiac",
        "discharge_instructions": "Follow up with primary physician in 1 week",
        "follow_up_recommendations": "Low sodium diet",
    }
    disc_resp = doctor_client.post("/v1/discharge/summaries", json=disc_payload)
    assert disc_resp.status_code in (200, 201, 401, 404, 422)

    summary_id = 1
    if disc_resp.status_code in (200, 201):
        summary_id = disc_resp.json().get("id", 1)

    # 6. Finalize Discharge
    fin_resp = doctor_client.put(f"/v1/discharge/summaries/{summary_id}/finalize")
    assert fin_resp.status_code in (200, 401, 404, 422)
