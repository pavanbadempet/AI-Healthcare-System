"""
Unit tests for SOTA Data Modeling Engine (backend/sota_data_modeling.py).
"""

from backend.sota_data_modeling import (
    BronzeRawRecord,
    SOTADataModelingEngine,
)


def test_medallion_pipeline_promotion():
    engine = SOTADataModelingEngine()
    bronze = BronzeRawRecord(raw_payload="MSH|^~\\&|HIS|HOSP|...", ingested_at=1700000000.0, source="HL7_v2")

    silver = engine.promote_bronze_to_silver(bronze, patient_id="PAT_999", mrn="MRN_12345")
    assert silver.patient_id == "PAT_999"
    assert len(silver.mrn_hash) == 64  # SHA256 hex string length

    gold = engine.generate_gold_analytics("FACILITY_01", [silver])
    assert gold.facility_id == "FACILITY_01"
    assert gold.total_patients == 1
    assert gold.icu_occupancy_rate == 0.75
