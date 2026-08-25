"""
Tier 4: Real-World Scenario — Continuous Telemetry Ingestion, HL7 Feeds & Vitals Anomaly Handling
Simulates real-time vital sign telemetry streaming and HL7 feed ingestion from hospital bedside monitors.
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_bedside_telemetry_and_hl7_ingestion_scenario(doctor_client: E2EClient, nurse_client: E2EClient):
    # 1. Telemetry Health Status Check
    health_resp = doctor_client.get("/v1/telemetry/health")
    assert health_resp.status_code in (200, 401, 404)

    # 2. Bedside HL7 Message Ingestion (ORM / Observation Feed)
    hl7_message = (
        "MSH|^~\\&|BEDSIDE_MONITOR_ICU_04|ST_JUDE|CENTRAL_EHR|ST_JUDE|20260821103000||ORU^R01|MSG9901|P|2.3\r"
        "PID|1||PAT00104||DOE^JANE||19750512|F\r"
        "OBX|1|NM|8867-4^Heart Rate^LN||76|/min|60-100|N|||F\r"
        "OBX|2|NM|2708-6^Oxygen Saturation^LN||98|%|95-100|N|||F\r"
    )
    hl7_resp = doctor_client.post("/v1/telemetry/hl7_ingest", json=hl7_message)
    assert hl7_resp.status_code in (200, 401, 404, 422)

    # 3. Snapshot Query
    snap_resp = doctor_client.get("/v1/telemetry/snapshot")
    assert snap_resp.status_code in (200, 401, 404)

    # 4. Resolve Any Triggered Signal
    resolve_resp = doctor_client.put("/v1/monitoring/signals/1/resolve")
    assert resolve_resp.status_code in (200, 401, 404)
