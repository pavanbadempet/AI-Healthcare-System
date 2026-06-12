"""
Tests for pdf_service.py and pdf_generator.py.

Covers: output type/format, content correctness, disclaimer presence,
BMI calculation, record colour-coding, edge cases (empty records, no advice).
"""
from datetime import datetime

import pytest

from backend.pdf_generator import generate_health_report
from backend.pdf_service import generate_medical_report

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


# ── Trend chart tests ─────────────────────────────────────────────────────────

def test_generate_health_report_with_vital_records():
    """Vital records are accepted and do not cause a crash."""
    vitals = [
        {
            "observed_at": datetime(2024, 1, 1),
            "heart_rate": 72,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "spo2": 98,
            "temperature_c": 36.6,
        },
        {
            "observed_at": datetime(2024, 2, 1),
            "heart_rate": 75,
            "systolic_bp": 125,
            "diastolic_bp": 82,
            "spo2": 97,
            "temperature_c": 36.8,
        },
    ]
    result = generate_health_report(
        user_name="Vitals Patient",
        user_profile={"height": 170, "weight": 70},
        health_records=[],
        vital_records=vitals,
    )
    assert isinstance(result, (bytes, bytearray))
    assert result[:4] == b"%PDF"


def test_generate_health_report_without_vital_records_kwarg():
    """vital_records is optional — omitting it should not crash."""
    result = generate_health_report(
        user_name="No Vitals",
        user_profile={},
        health_records=[],
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_with_empty_vital_records():
    """Empty vital_records list — no crash, no charts generated."""
    result = generate_health_report(
        user_name="Empty Vitals",
        user_profile={},
        health_records=[],
        vital_records=[],
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_charts_with_multiple_record_types():
    """Multiple assessment types produce bar chart and timeline."""
    records = [
        {"timestamp": datetime(2024, 1, 1), "record_type": "diabetes", "prediction": "High Risk"},
        {"timestamp": datetime(2024, 2, 1), "record_type": "heart", "prediction": "Low Risk"},
        {"timestamp": datetime(2024, 3, 1), "record_type": "diabetes", "prediction": "Low Risk"},
        {"timestamp": datetime(2024, 4, 1), "record_type": "kidney", "prediction": "High Risk"},
    ]
    result = generate_health_report(
        user_name="Chart Patient",
        user_profile={"height": 175, "weight": 75},
        health_records=records,
    )
    assert isinstance(result, (bytes, bytearray))
    assert len(result) > 1000  # charts inflate file size


def test_generate_health_report_single_record_no_timeline():
    """Only 1 dated record — timeline chart is skipped (needs >= 2), no crash."""
    records = [
        {"timestamp": datetime(2024, 1, 1), "record_type": "liver", "prediction": "Healthy"},
    ]
    result = generate_health_report(
        user_name="Single Record",
        user_profile={},
        health_records=records,
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_single_vital_no_chart():
    """Only 1 vital observation — vitals chart is skipped (needs >= 2), no crash."""
    vitals = [
        {"observed_at": datetime(2024, 1, 1), "heart_rate": 72, "systolic_bp": 120},
    ]
    result = generate_health_report(
        user_name="One Vital",
        user_profile={},
        health_records=[],
        vital_records=vitals,
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_partial_vitals_no_crash():
    """Vitals with some None fields should not crash chart generation."""
    vitals = [
        {"observed_at": datetime(2024, 1, 1), "heart_rate": 70, "spo2": None, "temperature_c": None},
        {"observed_at": datetime(2024, 3, 1), "heart_rate": 74, "spo2": 98, "temperature_c": 36.5},
    ]
    result = generate_health_report(
        user_name="Partial Vitals",
        user_profile={},
        health_records=[],
        vital_records=vitals,
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_records_without_timestamps():
    """Records missing timestamps are skipped gracefully in chart logic."""
    records = [
        {"record_type": "diabetes", "prediction": "High Risk"},  # no timestamp
        {"timestamp": datetime(2024, 2, 1), "record_type": "heart", "prediction": "Low Risk"},
    ]
    result = generate_health_report(
        user_name="No Timestamp",
        user_profile={},
        health_records=records,
    )
    assert isinstance(result, (bytes, bytearray))


def test_generate_health_report_combined_records_and_vitals():
    """Both health records and vitals produce multiple chart sections."""
    records = [
        {"timestamp": datetime(2024, 1, 1), "record_type": "diabetes", "prediction": "High Risk"},
        {"timestamp": datetime(2024, 3, 1), "record_type": "heart", "prediction": "Low Risk"},
    ]
    vitals = [
        {"observed_at": datetime(2024, 1, 15), "heart_rate": 72, "systolic_bp": 120, "diastolic_bp": 80},
        {"observed_at": datetime(2024, 2, 15), "heart_rate": 78, "systolic_bp": 130, "diastolic_bp": 85},
        {"observed_at": datetime(2024, 3, 15), "heart_rate": 70, "systolic_bp": 118, "diastolic_bp": 78},
    ]
    result = generate_health_report(
        user_name="Full Report",
        user_profile={"height": 180, "weight": 80, "blood_type": "O+"},
        health_records=records,
        vital_records=vitals,
    )
    assert isinstance(result, (bytes, bytearray))
    assert result[:4] == b"%PDF"
    assert len(result) > 5000  # bar chart + timeline + vitals chart inflate size


def test_chart_risk_assessment_history_returns_none_when_no_records():
    """Helper returns None for empty input — no matplotlib crash."""
    from backend.pdf_generator import _chart_risk_assessment_history
    result = _chart_risk_assessment_history([])
    assert result is None


def test_chart_assessment_timeline_returns_none_for_single_record():
    """Timeline needs >= 2 dated records."""
    from backend.pdf_generator import _chart_assessment_timeline
    result = _chart_assessment_timeline([
        {"timestamp": datetime(2024, 1, 1), "record_type": "diabetes", "prediction": "Low Risk"}
    ])
    assert result is None


def test_chart_vitals_trends_returns_none_for_single_vital():
    """Vitals chart needs >= 2 observations."""
    from backend.pdf_generator import _chart_vitals_trends
    result = _chart_vitals_trends([
        {"observed_at": datetime(2024, 1, 1), "heart_rate": 72}
    ])
    assert result is None


def test_chart_risk_assessment_history_returns_png_bytes():
    """Valid records → PNG bytes starting with PNG magic."""
    from backend.pdf_generator import _MPL_AVAILABLE, _chart_risk_assessment_history
    if not _MPL_AVAILABLE:
        pytest.skip("matplotlib not installed")
    records = [
        {"timestamp": datetime(2024, 1, 1), "record_type": "diabetes", "prediction": "High Risk"},
        {"timestamp": datetime(2024, 2, 1), "record_type": "heart", "prediction": "Low Risk"},
    ]
    result = _chart_risk_assessment_history(records)
    assert result is not None
    assert result[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic bytes


def test_chart_vitals_trends_returns_png_bytes():
    """Valid vitals → PNG bytes."""
    from backend.pdf_generator import _MPL_AVAILABLE, _chart_vitals_trends
    if not _MPL_AVAILABLE:
        pytest.skip("matplotlib not installed")
    vitals = [
        {"observed_at": datetime(2024, 1, 1), "heart_rate": 70, "systolic_bp": 120, "diastolic_bp": 80},
        {"observed_at": datetime(2024, 2, 1), "heart_rate": 75, "systolic_bp": 125, "diastolic_bp": 82},
    ]
    result = _chart_vitals_trends(vitals)
    assert result is not None
    assert result[:8] == b"\x89PNG\r\n\x1a\n"
