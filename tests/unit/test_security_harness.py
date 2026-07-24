"""
Unit tests for Security Pen-Test Harness
"""

from backend.security_pen_test_harness import security_harness


def test_audit_string_sanitization():
    clean, msg = security_harness.audit_string_sanitization("Patient John Doe presents with hypertension.")
    assert clean is True
    assert "clean" in msg

    dirty, msg = security_harness.audit_string_sanitization("<script>alert('xss')</script>")
    assert dirty is False
    assert "XSS" in msg


def test_audit_pii_log_redaction():
    clean_log = "User 42 executed query on patient ID 101. Status 200 OK."
    res = security_harness.audit_pii_log_redaction(clean_log)
    assert res["passed"] is True
    assert res["status"] == "PASS"

    dirty_log = "Error on user john.doe@example.com with SSN 123-45-6789"
    res = security_harness.audit_pii_log_redaction(dirty_log)
    assert res["passed"] is False
    assert res["leaked_email_count"] == 1
    assert res["leaked_ssn_count"] == 1
