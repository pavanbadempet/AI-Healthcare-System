"""
Unit tests for Medallion Lakehouse Engine (Bronze -> Silver -> Gold ETL Pipeline)
"""

from backend.medallion_lakehouse_engine import medallion_engine


def test_bronze_telemetry_ingestion():
    raw_payload = {"systolic_bp": 135, "diastolic_bp": 85, "heart_rate": 78, "spo2": 97}
    res = medallion_engine.ingest_bronze_telemetry(patient_id=101, raw_payload=raw_payload)

    assert res["layer"] == "BRONZE"
    assert res["patient_id"] == 101
    assert res["raw_payload"]["systolic_bp"] == 135


def test_silver_record_transformation():
    bronze = {
        "patient_id": 101,
        "raw_payload": {"systolic_bp": 142.5, "diastolic_bp": 92.0, "heart_rate": 84, "spo2": 96.0, "creatinine": 1.25},
    }
    silver = medallion_engine.transform_silver_patient_record(bronze)

    assert silver["layer"] == "SILVER"
    assert silver["patient_id"] == 101
    assert silver["systolic_bp"] == 142.5
    assert silver["data_quality_status"] == "VALIDATED"


def test_gold_kpi_aggregation():
    silvers = [
        {"patient_id": 1, "systolic_bp": 120.0, "diastolic_bp": 80.0, "heart_rate": 72.0, "spo2_percent": 98.0},
        {"patient_id": 2, "systolic_bp": 80.0, "diastolic_bp": 50.0, "heart_rate": 110.0, "spo2_percent": 88.0},  # high risk
    ]
    gold = medallion_engine.aggregate_gold_clinical_kpis(silvers)

    assert gold["layer"] == "GOLD"
    assert gold["total_patients"] == 2
    assert gold["mean_systolic_bp"] == 100.0
    assert gold["high_risk_patient_count"] == 1
    assert gold["high_risk_prevalence_percent"] == 50.0
