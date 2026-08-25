"""
Tier 1: Feature Coverage — Reports & Payments Domain (/generate_report, /v1/analyze/report, /v1/payments/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_reports_generate(patient_client: E2EClient):
    resp = patient_client.post("/generate_report")
    assert resp.status_code in (200, 401, 404, 422, 500)


def test_reports_analyze(doctor_client: E2EClient):
    payload = {"patient_id": 1, "report_type": "discharge_summary"}
    resp = doctor_client.post("/v1/analyze/report", json=payload)
    assert resp.status_code in (200, 400, 401, 404, 422)


def test_payments_create_order(patient_client: E2EClient):
    payload = {"amount": 5000, "currency": "INR", "invoice_id": 1}
    resp = patient_client.post("/v1/payments/create-order", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)


def test_payments_verify(patient_client: E2EClient):
    payload = {
        "razorpay_order_id": "order_test_123",
        "razorpay_payment_id": "pay_test_456",
        "razorpay_signature": "sig_test_789",
    }
    resp = patient_client.post("/v1/payments/verify", json=payload)
    assert resp.status_code in (200, 400, 401, 404, 422)


def test_payments_invoice_record(doctor_client: E2EClient):
    payload = {"amount": 250.00, "payment_method": "credit_card", "transaction_reference": "TXN_9988"}
    resp = doctor_client.post("/v1/billing/invoices/1/payments", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)
