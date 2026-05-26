import logging
from unittest.mock import patch

from backend import email_service


def test_booking_confirmation_simulation_does_not_log_email_or_names(monkeypatch, caplog):
    monkeypatch.delenv("SMTP_SERVER", raising=False)
    monkeypatch.delenv("SMTP_EMAIL", raising=False)
    caplog.set_level(logging.INFO, logger="backend.email_service")

    result = email_service.send_booking_confirmation(
        to_email="patient@example.com",
        patient_name="Sensitive Patient",
        doctor_name="Dr Sensitive",
        date_time="2026-05-27 10:00",
        link="https://video.example.com/secret",
    )

    assert result is True
    assert "patient@example.com" not in caplog.text
    assert "Sensitive Patient" not in caplog.text
    assert "Dr Sensitive" not in caplog.text
    assert "video.example.com/secret" not in caplog.text


def test_booking_confirmation_hides_smtp_exception_details(monkeypatch, caplog):
    monkeypatch.setenv("SMTP_SERVER", "smtp.example.com")
    monkeypatch.setenv("SMTP_EMAIL", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-password")
    sensitive_error = "SMTP failed password=smtp-secret patient_name=Sensitive User"
    caplog.set_level(logging.ERROR, logger="backend.email_service")

    with patch("smtplib.SMTP", side_effect=RuntimeError(sensitive_error)):
        result = email_service.send_booking_confirmation(
            to_email="patient@example.com",
            patient_name="Sensitive Patient",
            doctor_name="Dr Sensitive",
            date_time="2026-05-27 10:00",
            link="https://video.example.com/secret",
        )

    assert result is False
    assert sensitive_error not in caplog.text
    assert "smtp-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text
