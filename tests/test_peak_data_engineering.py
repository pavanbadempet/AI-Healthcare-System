"""
Comprehensive Test Suite for Peak Healthcare Data Engineering:
- OMOP CDM v5.4 Transformation & Concept Mapping (SNOMED, RxNorm, LOINC)
- Declarative Great Expectations Quality Gates & Quarantine Routing
- Delta Lake Time-Travel, Change Data Feed (CDF), and ACID Restore
- Lakehouse Data Engineering FastAPI Endpoints
"""

from fastapi.testclient import TestClient

from backend.data_platform.data_quality_gates import data_quality_gate
from backend.data_platform.delta_time_travel import delta_time_travel
from backend.data_platform.omop_cdm_engine import OMOPConceptMapper, omop_engine
from backend.main import app


def test_omop_concept_mapper():
    """Verifies that standard clinical terms resolve to official OMOP Concept IDs."""
    c_dm = OMOPConceptMapper.resolve_concept("Type 2 Diabetes Mellitus")
    assert c_dm["concept_id"] == 201826
    assert c_dm["vocab"] == "SNOMED"

    c_drug = OMOPConceptMapper.resolve_concept("Empagliflozin 10mg")
    assert c_drug["concept_id"] == 44816332
    assert c_drug["vocab"] == "RxNorm"

    c_sbp = OMOPConceptMapper.resolve_concept("systolic_bp")
    assert c_sbp["concept_id"] == 3004249
    assert c_sbp["vocab"] == "LOINC"


def test_omop_cdm_bundle_transformation():
    """Verifies relational transformation of patient data into OMOP CDM tables."""
    raw = {
        "patient_id": "PAT-OMOP-7788",
        "year_of_birth": 1968,
        "gender": "female",
        "conditions": ["Type 2 Diabetes", "Essential Hypertension"],
        "medications": ["Metformin", "Lisinopril"],
        "vitals": {
            "systolic_bp": 138.0,
            "diastolic_bp": 86.0,
            "fasting_glucose": 142.0,
            "hba1c": 7.6
        }
    }

    cdm = omop_engine.transform_patient_bundle(raw)
    assert "PERSON" in cdm
    assert "VISIT_OCCURRENCE" in cdm
    assert "CONDITION_OCCURRENCE" in cdm
    assert "DRUG_EXPOSURE" in cdm
    assert "MEASUREMENT" in cdm

    assert len(cdm["PERSON"]) == 1
    assert cdm["PERSON"][0]["gender_concept_id"] == 8532  # Female
    assert len(cdm["CONDITION_OCCURRENCE"]) == 2
    assert len(cdm["DRUG_EXPOSURE"]) == 2
    assert len(cdm["MEASUREMENT"]) == 4


def test_data_quality_gates_and_quarantine():
    """Verifies that Great Expectations cleanly splits valid rows from invalid quarantined rows."""
    batch = [
        {"patient_id": "P1", "timestamp": "2026-08-14T00:00:00Z", "heart_rate": 72, "systolic_bp": 120, "spo2": 98},
        {"patient_id": "P2", "timestamp": "2026-08-14T00:00:00Z", "heart_rate": 450, "systolic_bp": 130, "spo2": 99}, # Invalid HR (450 > 220)
        {"patient_id": None, "timestamp": "2026-08-14T00:00:00Z", "heart_rate": 80, "systolic_bp": 122, "spo2": 97}, # Null primary key
        {"patient_id": "P4", "timestamp": "2026-08-14T00:00:00Z", "heart_rate": 65, "systolic_bp": 118, "spo2": 35}  # Invalid SpO2 (35 < 50)
    ]

    clean, quarantined, summary = data_quality_gate.validate_and_partition_batch(batch)
    assert len(clean) == 1
    assert clean[0]["patient_id"] == "P1"
    assert len(quarantined) == 3
    assert summary["clean_count"] == 1
    assert summary["quarantined_count"] == 3
    assert summary["pass_rate_pct"] == 25.0


def test_delta_time_travel_and_restore():
    """Verifies Delta Lake history querying, point-in-time snapshot, and table restore."""
    table = "workspace.healthcare_silver.patients"

    # 1. History
    history = delta_time_travel.get_table_history(table)
    assert len(history) >= 1

    # 2. As of version
    snap = delta_time_travel.query_as_of_version(table, 0)
    assert snap["queried_version"] == 0
    assert snap["status"] == "SNAPSHOT_RETRIEVED"

    # 3. Restore
    res = delta_time_travel.restore_table_to_version(table, 0)
    assert res["status"] == "SUCCESSFULLY_RESTORED"
    assert "AUDIT-RESTORE" in res["hipaa_audit_log_id"]

    # 4. CDF
    cdf = delta_time_travel.compute_change_data_feed(table, 0, 2)
    assert len(cdf) == 2
    assert cdf[0]["_change_type"] == "insert"
    assert cdf[1]["_change_type"] == "update_postimage"


def test_data_engineering_fastapi_endpoints():
    """Verifies Lakehouse Data Engineering HTTP API endpoints."""
    client = TestClient(app)

    # 1. OMOP Transform
    omop_payload = {
        "patient_id": "PAT-API-01",
        "year_of_birth": 1980,
        "gender": "male",
        "conditions": ["Heart Failure"],
        "medications": ["Atorvastatin"],
        "vitals": {"heart_rate": 78, "systolic_bp": 125}
    }
    r_omop = client.post("/v1/lakehouse/omop/transform", json=omop_payload)
    assert r_omop.status_code == 200
    assert "PERSON" in r_omop.json()

    # 2. Quality Audit
    audit_payload = {
        "records": [
            {"patient_id": "P1", "timestamp": "2026-08-14T00:00:00Z", "heart_rate": 75, "systolic_bp": 120}
        ]
    }
    r_audit = client.post("/v1/lakehouse/quality/audit", json=audit_payload)
    assert r_audit.status_code == 200
    assert r_audit.json()["summary"]["pass_rate_pct"] == 100.0

    # 3. Delta History
    r_hist = client.get("/v1/lakehouse/delta/history")
    assert r_hist.status_code == 200
    assert isinstance(r_hist.json(), list)

    # 4. Delta Time Travel
    r_tt = client.post("/v1/lakehouse/delta/time-travel", json={"table_name": "workspace.healthcare_silver.patients", "target_version": 0})
    assert r_tt.status_code == 200
    assert r_tt.json()["status"] == "SNAPSHOT_RETRIEVED"

    # 5. Delta Restore
    r_rest = client.post("/v1/lakehouse/delta/restore", json={"table_name": "workspace.healthcare_silver.patients", "target_version": 0})
    assert r_rest.status_code == 200
    assert r_rest.json()["status"] == "SUCCESSFULLY_RESTORED"

    # 6. Delta CDF
    r_cdf = client.get("/v1/lakehouse/delta/cdf")
    assert r_cdf.status_code == 200
    assert len(r_cdf.json()) == 2
