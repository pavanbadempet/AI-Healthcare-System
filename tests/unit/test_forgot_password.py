import logging
from unittest.mock import patch

from backend import auth


def test_forgot_password_generic_response(client):
    # Register a test user
    client.post("/v1/signup", json={
        "username": "forgot_user",
        "password": "Password123!",
        "email": "forgot@example.com",
        "full_name": "Forgot User",
        "dob": "1990-01-01"
    })

    # Request reset link for existing email (using versioned endpoint)
    response_exist = client.post("/v1/forgot-password", json={"email": "forgot@example.com"})
    assert response_exist.status_code == 200
    assert response_exist.json()["status"] == "success"
    assert "reset link has been sent" in response_exist.json()["message"]

    # Request reset link for non-existing email (using versioned endpoint)
    response_non_exist = client.post("/v1/forgot-password", json={"email": "nonexistent@example.com"})
    assert response_non_exist.status_code == 200
    assert response_non_exist.json()["status"] == "success"
    assert "reset link has been sent" in response_non_exist.json()["message"]


def test_forgot_password_delivers_reset_link_without_logging_credentials(client, caplog):
    client.post("/v1/signup", json={
        "username": "private_reset_user",
        "password": "Password123!",
        "email": "private-reset@example.com",
        "full_name": "Private Reset User",
        "dob": "1990-01-01"
    })
    caplog.clear()

    with patch("backend.email_service.send_password_reset", return_value=True) as send_reset:
        with caplog.at_level(logging.INFO):
            response = client.post(
                "/v1/forgot-password",
                json={"email": "private-reset@example.com"},
            )

    assert response.status_code == 200
    delivery = send_reset.call_args.kwargs
    assert delivery["to_email"] == "private-reset@example.com"
    assert delivery["username"] == "private_reset_user"
    assert "reset-password?token=" in delivery["reset_link"]

    log_text = caplog.text
    assert delivery["reset_link"] not in log_text
    assert "private-reset@example.com" not in log_text
    assert "private_reset_user" not in log_text


def test_forgot_password_redirect(client):
    # Request via unversioned endpoint; should redirect to /v1 version
    # HTTP client follows redirect automatically by default, returning 200 from redirected route
    response = client.post("/forgot-password", json={"email": "nonexistent@example.com"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_reset_password_success(client, db_session):
    # Register user
    client.post("/v1/signup", json={
        "username": "reset_user",
        "password": "OldPassword123!",
        "email": "reset@example.com",
        "full_name": "Reset User",
        "dob": "1990-01-01"
    })

    # Generate a valid reset token
    token = auth.create_reset_token(email="reset@example.com", username="reset_user")

    # Reset password with valid token and strong new password
    response = client.post("/v1/reset-password", json={
        "token": token,
        "new_password": "NewPassword123!"
      })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify we can login with the new password
    login_response = client.post("/v1/token", data={
        "username": "reset_user",
        "password": "NewPassword123!"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_reset_password_weak_complexity(client):
    # Register user first so they exist in DB
    client.post("/v1/signup", json={
        "username": "weak_reset_user",
        "password": "OldPassword123!",
        "email": "weak_reset@example.com",
        "full_name": "Weak Reset User",
        "dob": "1990-01-01"
    })

    token = auth.create_reset_token(email="weak_reset@example.com", username="weak_reset_user")

    # Reset password with a weak new password (no numbers)
    response = client.post("/v1/reset-password", json={
        "token": token,
        "new_password": "weakpassword"
      })
    assert response.status_code == 400
    assert "at least 8 characters and contain both letters and numbers" in response.json()["detail"]


def test_reset_password_invalid_token(client):
    # Attempt to reset with a garbage token
    response = client.post("/v1/reset-password", json={
        "token": "invalid.jwt.token",
        "new_password": "NewPassword123!"
      })
    assert response.status_code == 400
    assert "Invalid or expired reset token" in response.json()["detail"]
