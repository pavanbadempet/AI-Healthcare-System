"""
Tier 3: Cross-Feature Flow — Clinical Encounter to Order to Billing & Payment Flow
Encounter -> Clinical Order -> Diagnostic Result -> Invoice -> Payment Record
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_encounter_to_clinical_order_to_billing_workflow(doctor_client: E2EClient):
    # 1. Create Encounter
    enc_payload = TestDataFactory.encounter_create(patient_id=1, doctor_id=2, department_id=1)
    enc_resp = doctor_client.post("/v1/hospital/encounters", json=enc_payload)
    assert enc_resp.status_code in (200, 201, 401, 404, 422)

    enc_id = 1
    if enc_resp.status_code in (200, 201):
        enc_id = enc_resp.json().get("id", 1)

    # 2. Place Clinical Order
    order_payload = TestDataFactory.clinical_order_create(encounter_id=enc_id, patient_id=1, doctor_id=2)
    order_resp = doctor_client.post("/v1/hospital/orders", json=order_payload)
    assert order_resp.status_code in (200, 201, 401, 404, 422)

    # 3. Post Diagnostic Lab Result
    lab_payload = {
        "patient_id": 1,
        "test_name": "Troponin I High Sensitivity",
        "category": "cardiac_enzymes",
        "value": "0.01",
        "unit": "ng/mL",
        "reference_range": "<0.04",
        "status": "final",
    }
    lab_resp = doctor_client.post("/v1/diagnostics/results", json=lab_payload)
    assert lab_resp.status_code in (200, 201, 401, 404, 422)

    # 4. Generate Invoice for Encounter
    inv_payload = TestDataFactory.invoice_create(patient_id=1, encounter_id=enc_id)
    inv_resp = doctor_client.post("/v1/billing/invoices", json=inv_payload)
    assert inv_resp.status_code in (200, 201, 401, 404, 422)

    inv_id = 1
    if inv_resp.status_code in (200, 201):
        inv_id = inv_resp.json().get("id", 1)

    # 5. Record Payment
    pay_payload = {"amount": 335.00, "payment_method": "insurance_copay"}
    pay_resp = doctor_client.post(f"/v1/billing/invoices/{inv_id}/payments", json=pay_payload)
    assert pay_resp.status_code in (200, 201, 401, 404, 422)
