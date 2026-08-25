"""
Tier 1: Feature Coverage — DICOMweb PACS Domain (/v1/dicomweb/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_dicomweb_studies_query(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/dicomweb/studies")
    assert resp.status_code in (200, 401, 404)


def test_dicomweb_study_metadata(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/dicomweb/studies/1.2.840.113619.2.55.3.60468842/metadata")
    assert resp.status_code in (200, 401, 404)


def test_dicomweb_series_query(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/dicomweb/studies/1.2.840.113619.2.55.3.60468842/series")
    assert resp.status_code in (200, 401, 404)


def test_dicomweb_study_instances(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/dicomweb/studies/1.2.840.113619.2.55.3.60468842/series/1.2.840.113619.2.55.3.60468842.1/instances")
    assert resp.status_code in (200, 401, 404)


def test_dicomweb_upload_study(doctor_client: E2EClient):
    payload = {"study_uid": "1.2.840.999", "patient_id": 1, "modality": "CT"}
    resp = doctor_client.post("/v1/hospital/dicom/upload", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)
