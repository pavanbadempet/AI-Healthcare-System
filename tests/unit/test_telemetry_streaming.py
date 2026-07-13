import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Ensure project root is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from scripts.runners.run_telemetry_streaming import (
    predict_heart_disease_risk,
    predict_lung_risk,
    process_conformed_record,
)
from scripts.runners.simulate_vitals_stream import generate_vitals


def test_vitals_generation():
    """Test that simulate_vitals_stream generates correct vitals schema."""
    patient = {"patient_id": 99, "facility_id": 1, "encounter_id": 123, "department_id": 4}

    # Generate normal vitals
    vitals_normal = generate_vitals(patient, anomaly_rate=0.0)
    assert vitals_normal["patient_id"] == 99
    assert vitals_normal["facility_id"] == 1
    assert vitals_normal["encounter_id"] == 123
    assert vitals_normal["department_id"] == 4
    assert 60 <= vitals_normal["heart_rate"] <= 95
    assert 95 <= vitals_normal["spo2"] <= 100
    assert 110 <= vitals_normal["systolic_bp"] <= 130
    assert "timestamp" in vitals_normal

    # Generate anomalous vitals
    vitals_anomaly = generate_vitals(patient, anomaly_rate=1.0)
    assert vitals_anomaly["patient_id"] == 99
    # Verify that at least one vital sign went out of normal range
    out_of_range = (
        vitals_anomaly["heart_rate"] > 100
        or vitals_anomaly["heart_rate"] < 60
        or vitals_anomaly["spo2"] < 95
        or vitals_anomaly["systolic_bp"] > 135
        or vitals_anomaly["temperature_c"] > 38.0
    )
    assert out_of_range


def test_predict_heart_disease_risk():
    """Verify heart risk prediction returns higher probability for extreme vitals."""
    # Stable vitals -> low risk
    low_risk = predict_heart_disease_risk(avg_hr=72.0, avg_systolic_bp=120.0)
    assert low_risk < 0.25

    # Severe vital breaches -> elevated risk
    high_risk = predict_heart_disease_risk(avg_hr=145.0, avg_systolic_bp=180.0)
    assert high_risk > 0.60
    assert high_risk > low_risk


def test_predict_lung_risk():
    """Verify lung risk prediction returns higher probability for extreme vitals."""
    # Stable vitals -> low risk
    low_risk = predict_lung_risk(avg_spo2=98.0, avg_resp_rate=14.0)
    assert low_risk < 0.20

    # Low oxygen (hypoxia) + tachypnea -> critical risk
    high_risk = predict_lung_risk(avg_spo2=87.0, avg_resp_rate=28.0)
    assert high_risk > 0.70
    assert high_risk > low_risk


def test_process_conformed_record_db_inserts():
    """Test process_conformed_record creates and saves vital observations and alerts to the database."""
    # Mock database session
    mock_db = MagicMock()

    # Mock the database query for rolling averages to return the current record's values
    mock_db.query.return_value.filter.return_value.first.return_value = (145.0, 175.0, 105.0, 89.0, 37.1, 25.0)

    # Create a dummy conformed vital stream record
    record = {
        "patient_id": 42,
        "heart_rate": 145.0,  # Cardiac anomaly
        "systolic_bp": 175.0,  # Severe hypertension
        "diastolic_bp": 105.0,
        "spo2": 89.0,  # Hypoxia anomaly
        "temperature_c": 37.1,
        "respiratory_rate": 25.0,
        "facility_id": 1,
        "encounter_id": 12,
        "department_id": 3,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Run the record processing
    process_conformed_record(mock_db, record)

    # Verify that database adds were triggered
    assert mock_db.add.call_count >= 1

    # Verify that conformed vital observations were added
    called_instances = [args[0] for args, _ in mock_db.add.call_args_list]

    vital_obs = [x for x in called_instances if x.__class__.__name__ == "VitalObservation"]
    assert len(vital_obs) == 1
    assert vital_obs[0].patient_id == 42
    assert vital_obs[0].heart_rate == 145.0
    assert vital_obs[0].spo2 == 89.0

    # Verify that a critical MonitoringSignal alert was created due to low SpO2/high HR
    monitoring_signals = [x for x in called_instances if x.__class__.__name__ == "MonitoringSignal"]
    assert len(monitoring_signals) == 1
    assert monitoring_signals[0].patient_id == 42
    assert monitoring_signals[0].severity == "critical"
    assert (
        "Hypoxia" in monitoring_signals[0].title
        or "Arrhythmia" in monitoring_signals[0].title
        or "Risk" in monitoring_signals[0].title
    )


def test_spark_streaming_metrics_logging():
    """Verify that process_batch successfully measures processing times and logs SparkStreamingMetrics."""
    mock_db = MagicMock()

    mock_row = MagicMock()
    mock_row.asDict.return_value = {
        "patient_id": 42,
        "heart_rate": 80.0,
        "systolic_bp": 120.0,
        "diastolic_bp": 80.0,
        "spo2": 98.0,
        "temperature_c": 37.0,
        "respiratory_rate": 14.0,
        "facility_id": 1,
        "encounter_id": 12,
        "department_id": 3,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    mock_df = MagicMock()
    mock_df.collect.return_value = [mock_row]

    with (
        patch("scripts.runners.run_telemetry_streaming.SessionLocal", return_value=mock_db),
        patch("scripts.runners.run_telemetry_streaming.load_ml_models"),
        patch("scripts.runners.run_telemetry_streaming.process_conformed_record", return_value=1.5) as mock_process_rec,
    ):
        from scripts.runners.run_telemetry_streaming import process_batch

        process_batch(mock_df, batch_id=123)

        mock_process_rec.assert_called_once()

        assert mock_db.add.call_count >= 1
        called_instances = [args[0] for args, _ in mock_db.add.call_args_list]

        metrics = [x for x in called_instances if x.__class__.__name__ == "SparkStreamingMetrics"]
        assert len(metrics) == 1
        assert metrics[0].batch_id == 123
        assert metrics[0].records_processed == 1
        assert metrics[0].processing_time_ms >= 0
        assert metrics[0].ml_latency_ms == 1.5
        mock_db.commit.assert_called_once()
