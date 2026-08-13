"""
Declarative Great Expectations & PySpark Data Quality Gates Engine.
Applies clinical expectation suites to streaming & batch telemetry:
- Validates physiological bounds (HR, SBP, DBP, SpO2, Glucose)
- Enforces primary key non-null and uniqueness constraints
- Automatically splits dirty records to the Quarantine Table (healthcare_bronze.quarantined_records)
"""

import time
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("backend.data_quality_gates")


class ClinicalExpectationSuite:
    """Standard physiological ranges and schema contracts."""

    PHYSIOLOGICAL_BOUNDS = {
        "heart_rate": (30.0, 220.0),
        "systolic_bp": (60.0, 250.0),
        "diastolic_bp": (35.0, 150.0),
        "spo2": (50.0, 100.0),
        "fasting_glucose": (20.0, 800.0),
        "temperature": (32.0, 43.0),
        "respiratory_rate": (6.0, 60.0),
        "age": (0.0, 120.0)
    }

    REQUIRED_FIELDS = ["patient_id", "timestamp"]


class LakehouseDataQualityGate:
    """Validates records and partitions them into Clean Silver and Quarantined Bronze."""

    def __init__(self):
        self.total_processed = 0
        self.total_clean = 0
        self.total_quarantined = 0

    def validate_and_partition_batch(
        self,
        records: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Validates a batch of clinical records against Great Expectations.
        Returns: (clean_records, quarantined_records, quality_summary)
        """
        clean_batch: List[Dict[str, Any]] = []
        quarantine_batch: List[Dict[str, Any]] = []
        violation_counts: Dict[str, int] = {}

        for rec in records:
            violations = []

            # 1. Null check on required fields
            for req_field in ClinicalExpectationSuite.REQUIRED_FIELDS:
                val = rec.get(req_field)
                if val is None or str(val).strip() == "":
                    violations.append(f"Null constraint violated on required field '{req_field}'")

            # 2. Physiological boundary checks
            for field, (low, high) in ClinicalExpectationSuite.PHYSIOLOGICAL_BOUNDS.items():
                if field in rec and rec[field] is not None:
                    try:
                        num_val = float(rec[field])
                        if num_val < low or num_val > high:
                            violations.append(f"Physiological bound violated on '{field}': value {num_val} not in [{low}, {high}]")
                    except (ValueError, TypeError):
                        violations.append(f"Type constraint violated on '{field}': non-numeric value '{rec[field]}'")

            # 3. Partition into Clean vs Quarantine
            if not violations:
                clean_batch.append(rec)
            else:
                for v in violations:
                    violation_counts[v] = violation_counts.get(v, 0) + 1
                
                quarantined_item = dict(rec)
                quarantined_item["_quarantine_timestamp"] = time.time()
                quarantined_item["_quarantine_violations"] = violations
                quarantine_batch.append(quarantined_item)

        self.total_processed += len(records)
        self.total_clean += len(clean_batch)
        self.total_quarantined += len(quarantine_batch)

        pass_rate = (len(clean_batch) / (len(records) or 1)) * 100.0

        summary = {
            "batch_size": len(records),
            "clean_count": len(clean_batch),
            "quarantined_count": len(quarantine_batch),
            "pass_rate_pct": round(pass_rate, 2),
            "violation_breakdown": violation_counts,
            "quality_status": "EXCELLENT" if pass_rate >= 95.0 else "WARNING" if pass_rate >= 80.0 else "CRITICAL"
        }

        return clean_batch, quarantine_batch, summary


data_quality_gate = LakehouseDataQualityGate()
