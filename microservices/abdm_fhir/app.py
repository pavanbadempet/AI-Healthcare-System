import os
import sys
from typing import Optional, Dict, Any, List
from types import SimpleNamespace

# Ensure repository root is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Ensure the microservice itself runs locally
os.environ["MICROSERVICES_MODE"] = "false"

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from backend.licensing import verify_license_key

def enforce_license():
    license_key = os.environ.get("LICENSE_KEY", "").strip()
    if not license_key:
        raise HTTPException(status_code=403, detail="License key required for premium microservices.")
    is_valid, reason = verify_license_key(license_key)
    if not is_valid:
        raise HTTPException(status_code=403, detail=f"Invalid license key: {reason}")

import clinical_fhir_abdm.fhir as fhir_lib
import clinical_fhir_abdm.abdm as abdm_lib

app = FastAPI(title="FHIR and ABDM Microservice", dependencies=[Depends(enforce_license)])

# --- FHIR Endpoints ---

@app.post("/fhir/patient")
def fhir_patient(payload: Dict[str, Any]):
    patient_data = payload.get("patient", {})
    patient_obj = SimpleNamespace(**patient_data)
    try:
        return fhir_lib.patient_resource(patient_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fhir/encounter")
def fhir_encounter(payload: Dict[str, Any]):
    encounter_data = payload.get("encounter", {})
    patient_id = payload.get("patient_id")
    encounter_obj = SimpleNamespace(**encounter_data)
    try:
        return fhir_lib.encounter_resource(encounter_obj, patient_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fhir/observation")
def fhir_observation(payload: Dict[str, Any]):
    observation_data = payload.get("observation", {})
    patient_id = payload.get("patient_id")
    observation_obj = SimpleNamespace(**observation_data)
    try:
        return fhir_lib.observation_resource(observation_obj, patient_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fhir/diagnostic_report")
def fhir_diagnostic_report(payload: Dict[str, Any]):
    result_data = payload.get("result", {})
    patient_id = payload.get("patient_id")
    result_obj = SimpleNamespace(**result_data)
    try:
        return fhir_lib.diagnostic_report_resource(result_obj, patient_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fhir/medication_request")
def fhir_medication_request(payload: Dict[str, Any]):
    prescription_data = payload.get("prescription", {})
    patient_id = payload.get("patient_id")
    prescription_obj = SimpleNamespace(**prescription_data)
    try:
        return fhir_lib.medication_request_resource(prescription_obj, patient_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fhir/invoice")
def fhir_invoice(payload: Dict[str, Any]):
    invoice_data = payload.get("invoice", {})
    patient_id = payload.get("patient_id")
    invoice_obj = SimpleNamespace(**invoice_data)
    try:
        return fhir_lib.invoice_resource(invoice_obj, patient_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fhir/care_event")
def fhir_care_event(payload: Dict[str, Any]):
    event_data = payload.get("event", {})
    patient_id = payload.get("patient_id")
    event_obj = SimpleNamespace(**event_data)
    try:
        return fhir_lib.care_event_resource(event_obj, patient_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fhir/build_bundle")
def fhir_build_bundle(payload: Dict[str, Any]):
    resources = payload.get("resources", [])
    try:
        return fhir_lib.build_bundle(resources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fhir/audit_event")
def fhir_audit_event(payload: Dict[str, Any]):
    audit_data = payload.get("audit_log", {})
    audit_obj = SimpleNamespace(**audit_data)
    try:
        return fhir_lib.audit_event_resource(audit_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ABDM Endpoints ---

@app.get("/abdm/settings")
def abdm_settings():
    try:
        settings = abdm_lib.get_settings()
        return {
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "abdm_url": settings.abdm_url,
            "consent_request_path": settings.consent_request_path,
            "configured": settings.configured_for_submission(),
            "missing_keys": settings.missing_for_submission()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/abdm/readiness")
def abdm_readiness():
    try:
        return abdm_lib.get_readiness()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/abdm/consent/callback")
def abdm_consent_callback(payload: Dict[str, Any]):
    try:
        return abdm_lib.normalize_consent_callback(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/abdm/consent/request")
def abdm_consent_request(payload: Dict[str, Any]):
    try:
        # Calls the prepare_consent_request function of the library
        res = abdm_lib.prepare_consent_request(
            patient_abha_address=payload.get("patient_abha_address"),
            purpose_code=payload.get("purpose_code"),
            hi_types=payload.get("hi_types"),
            date_from=payload.get("date_from"),
            date_to=payload.get("date_to"),
            data_erase_at=payload.get("data_erase_at"),
            requester_id=payload.get("requester_id"),
            consent_manager_id=payload.get("consent_manager_id")
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
