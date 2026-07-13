from unittest.mock import patch

from backend import auth, models, report

EXPECTED_ANALYSIS_DISCLAIMER = (
    "This AI-assisted report analysis is for informational support only and is not a medical diagnosis. "
    "Please consult a qualified clinician for diagnosis, treatment, or emergencies."
)


def _auth_headers(db_session, username: str = "report_user") -> dict[str, str]:
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


def test_report_analysis_requires_authentication(client):
    with patch("backend.report.vision_service.analyze_lab_report", return_value={"summary": "Healthy"}) as analyze:
        response = client.post(
            "/analyze/report",
            files={"file": ("report.jpg", b"fake-image", "image/jpeg")},
        )

    assert response.status_code == 401
    analyze.assert_not_called()


def test_report_analysis_allows_authenticated_user(client, db_session):
    headers = _auth_headers(db_session)
    expected = {"summary": "Healthy"}

    with patch("backend.report.vision_service.analyze_lab_report", return_value=expected) as analyze:
        response = client.post(
            "/analyze/report",
            files={"file": ("report.jpg", b"fake-image", "image/jpeg")},
            headers=headers,
        )

    assert response.status_code == 200
    assert response.json() == {**expected, "disclaimer": EXPECTED_ANALYSIS_DISCLAIMER}
    analyze.assert_called_once_with(b"fake-image")


def test_report_analysis_adds_medical_disclaimer(client, db_session):
    headers = _auth_headers(db_session, "report_disclaimer_user")

    with patch("backend.report.vision_service.analyze_lab_report", return_value={"summary": "Healthy"}):
        response = client.post(
            "/analyze/report",
            files={"file": ("report.jpg", b"fake-image", "image/jpeg")},
            headers=headers,
        )

    assert response.status_code == 200
    assert response.json()["disclaimer"] == EXPECTED_ANALYSIS_DISCLAIMER


def test_report_analysis_hides_provider_error_details(client, db_session, caplog):
    headers = _auth_headers(db_session, "report_error_user")
    sensitive_error = "vision failed patient_dob=1990-01-01 token=vision-secret"
    caplog.set_level("ERROR", logger="backend.report")

    with patch("backend.report.vision_service.analyze_lab_report", side_effect=Exception(sensitive_error)):
        response = client.post(
            "/analyze/report",
            files={"file": ("report.jpg", b"fake-image", "image/jpeg")},
            headers=headers,
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to analyze report"
    assert sensitive_error not in response.text
    assert "1990-01-01" not in response.text
    assert "vision-secret" not in response.text
    assert sensitive_error not in caplog.text
    assert "1990-01-01" not in caplog.text
    assert "vision-secret" not in caplog.text


def test_download_health_report_hides_pdf_error_details(client, db_session, caplog):
    headers = _auth_headers(db_session, "pdf_error_user")
    sensitive_error = "pdf failed patient_name=Sensitive User token=pdf-secret"
    caplog.set_level("ERROR", logger="backend.chat")

    with patch("backend.chat.pdf_generator.generate_health_report", side_effect=Exception(sensitive_error)):
        response = client.get("/download/health-report", headers=headers)

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to generate health report"
    assert sensitive_error not in response.text
    assert "Sensitive User" not in response.text
    assert "pdf-secret" not in response.text
    assert sensitive_error not in caplog.text
    assert "Sensitive User" not in caplog.text
    assert "pdf-secret" not in caplog.text


def test_download_health_report_uses_generic_filename(client, db_session):
    headers = _auth_headers(db_session, "filename_privacy_user")

    with patch("backend.chat.pdf_generator.generate_health_report", return_value=b"%PDF-1.4 fake"):
        response = client.get("/download/health-report", headers=headers)

    assert response.status_code == 200
    content_disposition = response.headers["content-disposition"]
    assert "filename_privacy_user" not in content_disposition
    assert content_disposition == "attachment; filename=Health_Report.pdf"


def test_report_module_download_uses_generic_filename(db_session):
    user = models.User(
        username="report_module_filename_user",
        email="report_module_filename_user@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role="patient",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    with patch("backend.report.pdf_service.generate_medical_report", return_value=b"%PDF-1.4 fake"):
        response = report.download_health_report(current_user=user, db=db_session)

    content_disposition = response.headers["content-disposition"]
    assert "report_module_filename_user" not in content_disposition
    assert content_disposition == "attachment; filename=Health_Report.pdf"
