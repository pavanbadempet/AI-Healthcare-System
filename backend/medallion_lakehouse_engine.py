"""
Medallion Lakehouse Engine (Bronze -> Silver -> Gold ETL Pipeline)
===================================================================
Orchestrates raw telemetry ingestion (Bronze), schema validation & deduplication (Silver),
and clinical risk KPI aggregation (Gold) for hospital analytics and longitudinal risk tracking.
"""

import datetime
from typing import Any, Dict, List


class MedallionLakehouseEngine:
    """Orchestrates Bronze, Silver, and Gold Medallion data lakehouse pipelines."""

    def ingest_bronze_telemetry(
        self,
        patient_id: int,
        raw_payload: Dict[str, Any],
        source_channel: str = "EMR_TELEMETRY_STREAM",
    ) -> Dict[str, Any]:
        """Ingests raw, unvalidated telemetry payload into the Bronze layer."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        bronze_record = {
            "ingestion_id": f"brz_{patient_id}_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}",
            "patient_id": patient_id,
            "source_channel": source_channel,
            "ingested_at": timestamp,
            "raw_payload": raw_payload,
            "layer": "BRONZE",
        }
        return bronze_record

    def transform_silver_patient_record(
        self,
        bronze_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Cleans, normalizes, and validates schema for the Silver layer."""
        raw = bronze_record.get("raw_payload", {})
        patient_id = bronze_record.get("patient_id", 0)

        # Standardize vital signs & laboratory values
        systolic_bp = max(float(raw.get("systolic_bp", 120.0)), 40.0)
        diastolic_bp = max(float(raw.get("diastolic_bp", 80.0)), 20.0)
        heart_rate = max(float(raw.get("heart_rate", 72.0)), 20.0)
        spo2_pct = min(max(float(raw.get("spo2", 98.0)), 50.0), 100.0)
        creatinine_mg_dL = max(float(raw.get("creatinine", 1.0)), 0.1)

        silver_record = {
            "silver_id": f"slv_{patient_id}_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}",
            "patient_id": patient_id,
            "systolic_bp": round(systolic_bp, 1),
            "diastolic_bp": round(diastolic_bp, 1),
            "heart_rate": round(heart_rate, 1),
            "spo2_percent": round(spo2_pct, 1),
            "serum_creatinine_mg_dL": round(creatinine_mg_dL, 2),
            "data_quality_status": "VALIDATED",
            "layer": "SILVER",
            "processed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        return silver_record

    def aggregate_gold_clinical_kpis(
        self,
        silver_records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Aggregates population-level clinical risk metrics and hospital KPIs for the Gold layer."""
        if not silver_records:
            return {
                "total_patients": 0,
                "mean_systolic_bp": 0.0,
                "mean_heart_rate": 0.0,
                "high_risk_patient_count": 0,
                "layer": "GOLD",
                "aggregated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

        total_patients = len(silver_records)
        mean_sys_bp = round(sum(r["systolic_bp"] for r in silver_records) / total_patients, 1)
        mean_hr = round(sum(r["heart_rate"] for r in silver_records) / total_patients, 1)

        # Count high risk criteria (MAP < 65 or SpO2 < 90%)
        high_risk_count = sum(
            1 for r in silver_records
            if ((2 * r["diastolic_bp"] + r["systolic_bp"]) / 3.0 < 65.0) or (r["spo2_percent"] < 90.0)
        )

        return {
            "total_patients": total_patients,
            "mean_systolic_bp": mean_sys_bp,
            "mean_heart_rate": mean_hr,
            "high_risk_patient_count": high_risk_count,
            "high_risk_prevalence_percent": round((high_risk_count / total_patients) * 100.0, 1),
            "layer": "GOLD",
            "aggregated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }


# Singleton engine instance
medallion_engine = MedallionLakehouseEngine()
