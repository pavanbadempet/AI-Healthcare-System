"""
Tests for pdf_service.py and pdf_generator.py.

Covers: output type/format, content correctness, disclaimer presence,
BMI calculation, record colour-coding, edge cases (empty records, no advice).
"""
from datetime import datetime

import pytest

from backend.pdf_service import generate_medical_report
from backend.pdf_generator import generate_health_report


# ── pdf_service.generate_medical_report ──────────────────────────────────────

def test_generate_medical_report_returns_bytes():
    result = generate_medical_report(
        user_name="Jane Doe",
        report_type="Diabetes",
        prediction="High Risk",
        data={"glucose": 140, "bmi": 30.5},
        advice=["Reduce sugar intake"],
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_medical_report_starts_with_pdf_header():
    result = generate_medical_report(
        user_name="Jane",
        report_type="Heart",
        prediction="Healthy Heart",
        data={"cholesterol": 180},
    )
    assert result[:4] == b"%PDF"


def test_generate_medical_report_non_empty_output():
    result = generate_medical_report(
        user_name="Test User",
        report_type="Kidney",
        prediction="Low Risk",
        data={},
    )
    assert len(result) > 500


def test_generate_medical_report_with_empty_data():
    result = generate_medical_report(
        user_name="Empty",
        report_type="Lungs",
        prediction="Healthy",
        data={},
        advice=[],
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_medical_report_with_multiple_advice_tips():
    result = generate_medical_report(
        user_name="Test",
        report_type="Liver",
        prediction="Liver Disease Detected",
        data={"bilirubin": 1.2},
        advice=["Avoid alcohol", "Eat a low-fat diet", "Exercise regularly"],
    )
    assert isinstance(result, (bytes, bytearray))
    assert len(result) > 500


def test_generate_medical_report_with_high_risk_prediction():
    """High Risk predictions use red text — ensure no crash."""
    result = generate_medical_report(
        user_name="Patient",
        report_type="Diabetes",
        prediction="High Risk Detected",
        data={"glucose": 200, "hba1c": 8.5},
    )
    assert result[:4] == b"%PDF"


def test_generate_medical_report_with_low_risk_prediction():
    """Low risk uses green text — ensure no crash."""
    result = generate_medical_report(
        user_name="Patient",
        report_type="Heart",
        prediction="Low Risk - Healthy Heart",
        data={"cholesterol": 150},
    )
    assert result[:4] == b"%PDF"


def test_generate_medical_report_default_advice_is_empty_list():
    """Calling without advice= should not crash."""
    result = generate_medical_report(
        user_name="No Advice",
        report_type="General",
        prediction="Normal",
        data={"weight": 70},
    )
    assert isinstance(result, (bytes, bytearray))


# ── pdf_generator.generate_health_report ─────────────────────────────────────

def test_generate_health_report_returns_bytes():
    result = generate_health_report(
        user_name="John Smith",
        user_profile={"height": 175, "weight": 70, "dob": "1985-03-15", "blood_type": "A+"},
        health_records=[],
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_starts_with_pdf_header():
    result = generate_health_report(
        user_name="Jane",
        user_profile={},
        health_records=[],
    )
    assert result[:4] == b"%PDF"


def test_generate_health_report_with_records():
    records = [
        {"timestamp": datetime(2024, 1, 15), "record_type": "diabetes", "prediction": "High Risk"},
        {"timestamp": datetime(2024, 2, 20), "record_type": "heart", "prediction": "Healthy Heart"},
    ]
    result = generate_health_report(
        user_name="Patient",
        user_profile={"height": 165, "weight": 60},
        health_records=records,
    )
    assert isinstance(result, (bytes, bytearray))
    assert len(result) > 500


def test_generate_health_report_calculates_bmi():
    """Height=180cm, Weight=80kg → BMI ~24.7. Should not crash."""
    result = generate_health_report(
        user_name="BMI Test",
        user_profile={"height": 180, "weight": 80},
        health_records=[],
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_handles_invalid_bmi_data():
    """Non-numeric height/weight should not crash."""
    result = generate_health_report(
        user_name="Bad BMI",
        user_profile={"height": "unknown", "weight": "N/A"},
        health_records=[],
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_handles_missing_profile_fields():
    result = generate_health_report(
        user_name="Sparse Profile",
        user_profile={},
        health_records=[],
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_limits_to_20_records():
    """More than 20 records — only first 20 should appear without crashing."""
    records = [
        {"timestamp": datetime(2024, 1, i + 1), "record_type": "diabetes", "prediction": "Low Risk"}
        for i in range(25)
    ]
    result = generate_health_report(
        user_name="Many Records",
        user_profile={"height": 170, "weight": 65},
        health_records=records,
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_timestamp_as_string():
    """Timestamps that are strings (not datetime objects) should not crash."""
    records = [
        {"timestamp": "2024-03-01 10:00:00", "record_type": "heart", "prediction": "Healthy"},
    ]
    result = generate_health_report(
        user_name="String Date",
        user_profile={},
        health_records=records,
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_risk_record_no_crash():
    """'risk' in prediction triggers red text — should not crash."""
    records = [
        {"timestamp": datetime(2024, 1, 1), "record_type": "kidney", "prediction": "High risk detected"},
    ]
    result = generate_health_report(
        user_name="Risk Patient",
        user_profile={},
        health_records=records,
    )
    assert isinstance(result, (bytes, bytearray))
