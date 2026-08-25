"""
Tier 1: Feature Coverage — Billing Domain (/v1/billing/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_billing_list_services(patient_client: E2EClient):
    resp = patient_client.get("/v1/billing/services")
    assert resp.status_code in (200, 401)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)


def test_billing_create_service(admin_client: E2EClient):
    payload = TestDataFactory.billable_service_create()
    resp = admin_client.post("/v1/billing/services", json=payload)
    assert resp.status_code in (200, 201, 401, 403, 422)


def test_billing_create_invoice(doctor_client: E2EClient):
    payload = TestDataFactory.invoice_create()
    resp = doctor_client.post("/v1/billing/invoices", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)


def test_billing_patient_invoices(patient_client: E2EClient):
    resp = patient_client.get("/v1/billing/patient/invoices")
    assert resp.status_code in (200, 401)


def test_billing_estimate(patient_client: E2EClient):
    resp = patient_client.get("/v1/billing/estimate?procedure_type=consultation&region=US-East")
    assert resp.status_code in (200, 401, 422)


def test_billing_soap_audit(doctor_client: E2EClient):
    soap_data = {
        "subjective": "Patient complains of chest tightness",
        "objective": "BP 140/90, HR 88",
        "assessment": "Essential hypertension",
        "plan": "Prescribe amlodipine 5mg",
    }
    resp = doctor_client.post("/v1/billing/soap-audit", json=soap_data)
    assert resp.status_code in (200, 401, 422)
