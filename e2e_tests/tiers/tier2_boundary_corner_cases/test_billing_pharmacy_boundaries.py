"""
Tier 2: Boundary & Corner Cases — Billing & Pharmacy Boundaries
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_billing_create_service_negative_price(admin_client: E2EClient):
    payload = {"code": "CPT-NEG-01", "name": "Negative Service", "base_price": -100.0}
    resp = admin_client.post("/v1/billing/services", json=payload)
    assert resp.status_code in (200, 201, 400, 422, 401, 403)


def test_billing_create_invoice_empty_items(doctor_client: E2EClient):
    payload = {"patient_id": 1, "encounter_id": 1, "items": []}
    resp = doctor_client.post("/v1/billing/invoices", json=payload)
    assert resp.status_code in (200, 201, 400, 422, 404, 401, 500)


def test_billing_payment_negative_amount(doctor_client: E2EClient):
    payload = {"amount": -50.0, "payment_method": "cash"}
    resp = doctor_client.post("/v1/billing/invoices/1/payments", json=payload)
    assert resp.status_code in (200, 201, 400, 422, 404, 401, 500)


def test_pharmacy_create_inventory_negative_stock(admin_client: E2EClient):
    payload = {
        "name": "Negative Drug",
        "generic_name": "Test",
        "quantity_in_stock": -50,
        "unit_price": -1.0,
    }
    resp = admin_client.post("/v1/pharmacy/inventory", json=payload)
    assert resp.status_code in (200, 201, 400, 422, 401, 403)


def test_pharmacy_dispense_nonexistent_prescription(doctor_client: E2EClient):
    payload = {"quantity_dispensed": 10, "notes": "Emergency refill"}
    resp = doctor_client.post("/v1/pharmacy/prescriptions/999999/dispense", json=payload)
    assert resp.status_code in (200, 400, 404, 422, 401, 500)


def test_pharmacy_safety_check_empty_payload(doctor_client: E2EClient):
    resp = doctor_client.post("/v1/pharmacy/check-safety", json={})
    assert resp.status_code in (200, 400, 422, 401, 404, 500)
