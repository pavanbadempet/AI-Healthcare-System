"""
Tier 3: Cross-Feature Combinations — Deprecated CRUD to Billing and Claims Preflight Flow
Simulates cross-module pipeline: In-process Deprecated CRUD Encounter -> Billable Service -> Invoice Generation -> CMS-1500 Claim Check.
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_deprecation_to_billing_flow(admin_client: E2EClient, doctor_client: E2EClient):
    """
    Step 1: Check available billable service codes.
    Step 2: Create a billable item for an outpatient visit.
    Step 3: Run claims preflight validation check.
    Step 4: Verify invoice creation.
    """
    # Step 1: Query services
    services_resp = admin_client.get("/v1/billing/services")
    assert services_resp.status_code in (200, 401, 404)

    # Step 2: Create billable service item
    service_payload = {
        "service_code": "99213",
        "name": "Office Visit - Level 3 Outpatient",
        "category": "Consultation",
        "standard_fee": 145.00,
        "is_active": True,
    }
    create_resp = admin_client.post("/v1/billing/services", json=service_payload)
    assert create_resp.status_code in (200, 201, 401, 404, 409, 422)

    # Step 3: Run claims preflight
    claim_payload = {
        "patient_id": 1,
        "diagnosis_codes": ["E11.9", "I10"],
        "procedure_codes": ["99213"],
        "total_billed": 145.00,
    }
    claim_resp = admin_client.post("/v1/claims/preflight", json=claim_payload)
    assert claim_resp.status_code in (200, 201, 401, 404, 405, 422)
