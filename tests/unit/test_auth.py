import pytest
from fastapi.testclient import TestClient

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
