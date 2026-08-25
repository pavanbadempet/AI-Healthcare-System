"""
Tier 1: Feature Coverage — Telemetry Domain (/v1/telemetry/* & /telemetry/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_telemetry_health_v1(e2e_client: E2EClient):
    resp = e2e_client.get("/v1/telemetry/health")
    assert resp.status_code in (200, 404)


def test_telemetry_health_root(e2e_client: E2EClient):
    resp = e2e_client.get("/telemetry/health")
    assert resp.status_code in (200, 404)


def test_telemetry_snapshot_v1(patient_client: E2EClient):
    resp = patient_client.get("/v1/telemetry/snapshot")
    assert resp.status_code in (200, 401, 404)


def test_telemetry_snapshot_root(patient_client: E2EClient):
    resp = patient_client.get("/telemetry/snapshot")
    assert resp.status_code in (200, 401, 404)


def test_telemetry_hl7_ingest_v1(doctor_client: E2EClient):
    hl7_sample = "MSH|^~\\&|SENDING_APP|SENDING_FAC|REC_APP|REC_FAC|20260821||ORM^O01|MSG001|P|2.3\rPID|1||PAT001||DOE^JOHN||19800101|M\r"
    resp = doctor_client.post("/v1/telemetry/hl7_ingest", json=hl7_sample)
    assert resp.status_code in (200, 401, 422)


def test_telemetry_hl7_ingest_root(doctor_client: E2EClient):
    hl7_sample = "MSH|^~\\&|SENDING_APP|SENDING_FAC|REC_APP|REC_FAC|20260821||ORM^O01|MSG001|P|2.3\rPID|1||PAT001||DOE^JOHN||19800101|M\r"
    resp = doctor_client.post("/telemetry/hl7_ingest", json=hl7_sample)
    assert resp.status_code in (200, 401, 422)
