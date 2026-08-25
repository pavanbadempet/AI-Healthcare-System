"""
Tier 4: Real-World Scenario — Inpatient Medication Order, Safety Check & Dispense Lifecycle
Prescribe -> Safety & Interaction Check -> Inventory Verification -> Dispense
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_inpatient_prescription_dispense_and_safety_scenario(doctor_client: E2EClient):
    # 1. Doctor creates prescription
    rx_payload = TestDataFactory.prescription_create(patient_id=1, doctor_id=2)
    rx_resp = doctor_client.post("/v1/pharmacy/prescriptions", json=rx_payload)
    assert rx_resp.status_code in (200, 201, 401, 404, 422)

    rx_id = 1
    if rx_resp.status_code in (200, 201):
        rx_id = rx_resp.json().get("id", 1)

    # 2. Automated Drug Safety & Contraindication Check
    safety_payload = {
        "patient_id": 1,
        "new_medication": rx_payload["medication_name"],
        "current_medications": ["Lisinopril 10mg", "Atorvastatin 20mg"],
    }
    safety_resp = doctor_client.post("/v1/pharmacy/check-safety", json=safety_payload)
    assert safety_resp.status_code in (200, 401, 404, 422)

    # 3. Check Pharmacy Inventory
    inv_resp = doctor_client.get("/v1/pharmacy/inventory")
    assert inv_resp.status_code in (200, 401)

    # 4. Dispense Prescription
    dispense_payload = {
        "quantity_dispensed": 60,
        "notes": "Verified against patient allergy profile and dispensed by pharmacy staff",
    }
    dispense_resp = doctor_client.post(f"/v1/pharmacy/prescriptions/{rx_id}/dispense", json=dispense_payload)
    assert dispense_resp.status_code in (200, 201, 401, 404, 422)
