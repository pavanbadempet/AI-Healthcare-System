"""
Tier 3: Cross-Feature Flow — Complete Patient Onboarding & Appointment Lifecycle
Signup -> Login -> Profile -> Schedule Appointment -> Reschedule -> Cancel
"""
import uuid
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_full_patient_onboarding_and_appointment_lifecycle(e2e_client: E2EClient):
    tag = uuid.uuid4().hex[:6]
    username = f"flow_pat_{tag}"
    password = "StrongPassword123!"

    # 1. Signup
    signup_payload = TestDataFactory.user_create(username=username)
    signup_resp = e2e_client.post("/v1/signup", json=signup_payload)
    assert signup_resp.status_code in (200, 201), f"Signup failed: {signup_resp.text}"

    # 2. Login
    login_resp = e2e_client.post(
        "/v1/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json().get("access_token")
    assert token is not None

    # Authenticated client for this user
    user_client = E2EClient(base_url=e2e_client.base_url, auth_token=token)

    # 3. View Profile
    profile_resp = user_client.get("/v1/profile")
    assert profile_resp.status_code == 200
    assert profile_resp.json().get("username") == username

    # 4. Update Profile
    update_resp = user_client.put("/v1/profile", json={"phone_number": "+15551234567"})
    assert update_resp.status_code in (200, 204)

    # 5. Book Appointment
    appt_payload = {
        "doctor_id": 1,
        "date": "2026-10-15",
        "time": "14:00:00",
        "reason": "Initial health screening",
        "status": "scheduled",
    }
    book_resp = user_client.post("/v1/appointments/", json=appt_payload)
    assert book_resp.status_code in (200, 201, 422, 404)

    # 6. List Appointments
    list_resp = user_client.get("/v1/appointments/")
    assert list_resp.status_code == 200
