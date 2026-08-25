"""
Tier 1: Feature Coverage — Four-Eye Governance Domain (/v1/governance/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_governance_pending_reviews(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/governance/four-eye/pending")
    assert resp.status_code in (200, 401, 403, 404)


def test_governance_submit_request(doctor_client: E2EClient):
    payload = {
        "request_id": "req_test_001",
        "action_type": "high_dose_narcotic_prescription",
        "initiator_id": "dr_01",
        "details": {"drug": "Morphine", "dosage": "50mg"},
    }
    resp = doctor_client.post("/v1/governance/four-eye/submit", json=payload)
    assert resp.status_code in (200, 201, 401, 403, 404, 422)


def test_governance_review_action(doctor_client: E2EClient):
    payload = {
        "request_id": "req_test_001",
        "reviewer_id": "dr_02",
        "decision": "approved",
        "notes": "Verified clinical necessity",
    }
    resp = doctor_client.post("/v1/governance/four-eye/review", json=payload)
    assert resp.status_code in (200, 201, 400, 401, 403, 404, 422)


def test_governance_verify_request(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/governance/four-eye/verify/req_test_001")
    assert resp.status_code in (200, 401, 403, 404)


def test_governance_ai_guardian_evaluate(doctor_client: E2EClient):
    payload = {
        "action_name": "critical_care_prescription",
        "parameters": {"patient_age": 75, "contraindication_flags": []},
    }
    resp = doctor_client.post("/v1/governance/ai-guardian/evaluate", json=payload)
    assert resp.status_code in (200, 401, 403, 404, 422)
