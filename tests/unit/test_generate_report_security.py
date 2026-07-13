from unittest.mock import patch

import pytest
from fastapi import HTTPException

from backend import auth, main, models


class JsonRequest:
    async def json(self):
        return _payload()


def _auth_headers(db_session, username: str = "report_pdf_user") -> dict[str, str]:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role="patient",
    )
    db_session.add(user)
    db_session.commit()

    token = auth.create_access_token({"sub": username})
    return {"Authorization": f"Bearer {token}"}


def _payload() -> dict:
    return {
        "user_name": "Test Patient",
        "report_type": "Diabetes Screening",
        "prediction": "Low Risk",
        "data": {"glucose": 95, "bmi": 23},
        "advice": ["Follow up with a qualified clinician for medical decisions."],
    }


def test_generate_report_requires_authentication(client):
    with patch("backend.main.generate_medical_report", return_value=b"%PDF-1.4") as generate:
        response = client.post("/generate_report", json=_payload())

    assert response.status_code == 401
    generate.assert_not_called()


def test_generate_report_allows_authenticated_user(client, db_session):
    headers = _auth_headers(db_session)

    with patch("backend.main.generate_medical_report", return_value=b"%PDF-1.4") as generate:
        response = client.post("/generate_report", json=_payload(), headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4"
    generate.assert_called_once_with(
        user_name="report_pdf_user",
        report_type="Diabetes Screening",
        prediction="Low Risk",
        data={"glucose": 95, "bmi": 23},
        advice=["Follow up with a qualified clinician for medical decisions."],
    )


def test_generate_report_ignores_request_user_name(client, db_session):
    headers = _auth_headers(db_session, "safe_report_user")
    payload = _payload()
    payload["user_name"] = "Another Patient"

    with patch("backend.main.generate_medical_report", return_value=b"%PDF-1.4") as generate:
        response = client.post("/generate_report", json=payload, headers=headers)

    assert response.status_code == 200
    assert generate.call_args.kwargs["user_name"] == "safe_report_user"


@pytest.mark.asyncio
async def test_generate_report_hides_pdf_error_details(caplog):
    user = models.User(id=1, username="pdf_route_user", role="patient")
    sensitive_error = "pdf failed patient_name=Sensitive User token=pdf-secret"
    caplog.set_level("ERROR", logger="backend.main")

    with patch("backend.main.generate_medical_report", side_effect=Exception(sensitive_error)):
        with pytest.raises(HTTPException) as exc_info:
            await main.generate_report(JsonRequest(), current_user=user)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to generate report"
    assert sensitive_error not in caplog.text
    assert "Sensitive User" not in caplog.text
    assert "pdf-secret" not in caplog.text
