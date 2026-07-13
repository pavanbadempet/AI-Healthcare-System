from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from backend import auth, models


def _create_facility(db_session, name: str) -> models.HospitalFacility:
    facility = models.HospitalFacility(
        name=name,
        facility_type="hospital",
        country="IN",
        status="active",
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)
    return facility


def _create_user(
    db_session,
    username: str,
    role: str,
    *,
    facility_id: int | None = None,
) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=auth.get_password_hash("Password123!"),
        role=role,
        facility_id=facility_id,
        allow_data_collection=1,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token({'sub': username})}"}


@pytest.fixture
def auth_header(client):
    # Setup - Create User
    client.post("/signup", json={
        "username": "test_user_unique",
        "password": "Password123!",
        "email": "unique@example.com",
        "full_name": "Unique User",
        "dob": "1995-05-05"
    })
    # Login to get token
    response = client.post("/token", data={
        "username": "test_user_unique",
        "password": "Password123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_signup_success(client):
    response = client.post("/signup", json={
        "username": "newuser",
        "password": "Password123!",
        "email": "new@example.com",
        "full_name": "New User",
        "dob": "1995-05-05"
    })
    if response.status_code != 200:
        print(f"[DEBUG] Response Body: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data

def test_signup_duplicate_username(client):
    # Create first
    client.post("/signup", json={
        "username": "dupuser",
        "password": "Password123!",
        "email": "dup@example.com",
        "full_name": "Dup User",
        "dob": "1995-05-05"
    })
    # Create duplicate
    response = client.post("/signup", json={
        "username": "dupuser",
        "password": "Password123!",
        "email": "dup2@example.com", # Diff email
        "full_name": "Dup User 2",
        "dob": "1995-05-05"
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_signup_weak_password(client):
    response = client.post("/signup", json={
        "username": "weakpw",
        "password": "123", # Too short
        "email": "weak@example.com",
        "full_name": "Weak Pw",
        "dob": "1995-05-05"
    })
    assert response.status_code == 400 # Expect 400 from custom validation, not 422
    # assert "at least 8 characters" in response.json()["detail"]

def test_signup_hides_unexpected_error_details(client, caplog):
    sensitive_error = "hash failed password=Password123! email=leaky@example.com"
    caplog.set_level("ERROR", logger="backend.auth")

    with patch("backend.auth.get_password_hash", side_effect=Exception(sensitive_error)):
        response = client.post("/signup", json={
            "username": "leakyuser",
            "password": "Password123!",
            "email": "leaky@example.com",
            "full_name": "Leaky User",
            "dob": "1995-05-05"
        })

    assert response.status_code == 500
    assert response.json()["detail"] == "Signup failed. Please try again later."
    assert sensitive_error not in response.text
    assert "Password123!" not in response.text
    assert "leaky@example.com" not in response.text
    assert sensitive_error not in caplog.text
    assert "Password123!" not in caplog.text
    assert "leaky@example.com" not in caplog.text

def test_login_success(client):
    # Setup
    client.post("/signup", json={
        "username": "loginuser",
        "password": "Password123!",
        "email": "login@example.com",
        "full_name": "Login User",
        "dob": "1995-05-05"
    })
    # Login
    response = client.post("/token", data={
        "username": "loginuser",
        "password": "Password123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_hides_audit_error_details(client, caplog):
    client.post("/signup", json={
        "username": "audituser",
        "password": "Password123!",
        "email": "audit@example.com",
        "full_name": "Audit User",
        "dob": "1995-05-05"
    })
    sensitive_error = "audit failed email=audit@example.com token=secret-token"
    caplog.set_level("ERROR", logger="backend.auth")

    with patch("backend.auth.models.AuditLog", side_effect=Exception(sensitive_error)):
        response = client.post("/token", data={
            "username": "audituser",
            "password": "Password123!"
        })

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert sensitive_error not in response.text
    assert "audit@example.com" not in response.text
    assert "secret-token" not in response.text
    assert sensitive_error not in caplog.text
    assert "audit@example.com" not in caplog.text
    assert "secret-token" not in caplog.text

def test_login_hides_unexpected_error_details(caplog):
    sensitive_error = "login query failed username=login_leak password=Password123!"
    mock_db = MagicMock()
    mock_db.query.side_effect = Exception(sensitive_error)
    form = OAuth2PasswordRequestForm(username="login_leak", password="Password123!")
    caplog.set_level("ERROR", logger="backend.auth")

    with pytest.raises(HTTPException) as exc_info:
        auth.login_for_access_token(form_data=form, db=mock_db)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Login failed. Please try again later."
    assert sensitive_error not in caplog.text
    assert "login_leak" not in caplog.text
    assert "Password123!" not in caplog.text

def test_login_invalid_password(client):
    client.post("/signup", json={
        "username": "badpwuser",
        "password": "Password123!",
        "email": "badpw@example.com",
        "full_name": "Bad PW",
        "dob": "1995-05-05"
    })
    response = client.post("/token", data={
        "username": "badpwuser",
        "password": "WrongPassword!"
    })
    assert response.status_code == 401

def test_protected_route_access(client, auth_header):
    # Use actual existing endpoint /profile
    response = client.get("/profile", headers=auth_header)
    assert response.status_code == 200
    assert response.json()["username"] == "test_user_unique"

def test_protected_route_no_token(client):
    response = client.get("/profile")
    assert response.status_code == 401


def test_facility_admin_users_route_is_scoped_to_own_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Auth Users Primary")
    other_facility = _create_facility(db_session, "Auth Users Other")
    admin = _create_user(db_session, "auth_users_facility_admin", "admin", facility_id=primary_facility.id)
    local_patient = _create_user(db_session, "auth_users_local_patient", "patient", facility_id=primary_facility.id)
    other_patient = _create_user(db_session, "auth_users_other_patient", "patient", facility_id=other_facility.id)
    _create_user(db_session, "auth_users_unassigned_patient", "patient")
    admin_username = admin.username
    local_patient_username = local_patient.username
    other_patient_username = other_patient.username

    response = client.get("/users", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    usernames = {user["username"] for user in response.json()}
    assert admin_username in usernames
    assert local_patient_username in usernames
    assert other_patient_username not in usernames
    assert "auth_users_unassigned_patient" not in usernames


def test_facility_admin_full_user_details_rejects_other_facility_user(client, db_session):
    primary_facility = _create_facility(db_session, "Auth Full Primary")
    other_facility = _create_facility(db_session, "Auth Full Other")
    admin = _create_user(db_session, "auth_full_facility_admin", "admin", facility_id=primary_facility.id)
    patient = _create_user(db_session, "auth_full_other_patient", "patient", facility_id=other_facility.id)

    response = client.get(f"/users/{patient.id}/full", headers=_auth_headers(admin.username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin resource is outside the user's facility"


def test_user_full_details_hides_audit_error_details(client, db_session, caplog):
    admin = models.User(
        username="full_admin",
        email="full_admin@example.com",
        hashed_password=auth.get_password_hash("Password123!"),
        role="admin",
    )
    patient = models.User(
        username="full_patient",
        email="full_patient@example.com",
        hashed_password=auth.get_password_hash("Password123!"),
        role="patient",
        allow_data_collection=1,
    )
    db_session.add_all([admin, patient])
    db_session.commit()
    db_session.refresh(patient)
    headers = {"Authorization": f"Bearer {auth.create_access_token({'sub': admin.username})}"}
    sensitive_error = "audit insert failed db_password=secret-db-password"
    caplog.set_level("ERROR", logger="backend.auth")

    with patch("backend.auth.models.AuditLog", side_effect=Exception(sensitive_error)):
        response = client.get(f"/users/{patient.id}/full", headers=headers)

    assert response.status_code == 200
    assert response.json()["username"] == "full_patient"
    assert sensitive_error not in caplog.text
    assert "secret-db-password" not in caplog.text
