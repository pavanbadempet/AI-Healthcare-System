import os
import sys
from datetime import datetime, timedelta, timezone
from backend import models
from backend.database import get_db
from backend.model_service import model_service
from backend.tee_enclave import ConfidentialEnclave, TRUSTED_MODEL_HASHES

def test_unmocked_clinical_e2e_flow(client, db_session):
    """
    High-value, unmocked integration test that exercises the entire
    clinical lifecycle:
    1. Register patient & doctor.
    2. Log real vital observations to DB.
    3. Grant interoperability consent.
    4. Query ABDM FHIR bundle export (verifying DB records are fetched dynamically).
    5. Run real TEE-attested ML disease prediction (bypassing testing mocks).
    """
    # Clear secure boot registry to verify TEE secure bootstrap works
    TRUSTED_MODEL_HASHES.clear()

    original_license = os.environ.get("LICENSE_KEY")
    os.environ["LICENSE_KEY"] = "CLINIC-TRIAL-2026"

    # --- 1. SETUP USERS ---
    patient_username = "alice_patient_e2e"
    doctor_username = "bob_doctor_e2e"
    password = "StrongPassword123!"

    # Create Patient
    patient_res = client.post("/signup", json={
        "username": patient_username,
        "password": password,
        "email": "alice@example.com",
        "full_name": "Alice Patient E2E",
        "dob": "1980-05-15",
        "gender": "female"
    })
    assert patient_res.status_code == 200
    patient_id = patient_res.json()["id"]

    # Create Doctor
    doctor_res = client.post("/signup", json={
        "username": doctor_username,
        "password": password,
        "email": "bob@example.com",
        "full_name": "Bob Doctor E2E",
        "dob": "1975-08-20"
    })
    assert doctor_res.status_code == 200
    doctor_id = doctor_res.json()["id"]

    # Assign doctor role
    db_patient = db_session.query(models.User).filter_by(id=patient_id).first()
    db_doctor = db_session.query(models.User).filter_by(id=doctor_id).first()
    db_doctor.role = "doctor"
    db_doctor.specialization = "Cardiologist"
    db_session.commit()

    # Create active encounter to establish access relation
    encounter = models.Encounter(
        patient_id=patient_id,
        doctor_id=doctor_id,
        status="open",
        encounter_type="AMB",
        started_at=datetime.now()
    )
    db_session.add(encounter)
    db_session.commit()
    db_session.refresh(encounter)

    # --- 2. LOG VITAL OBSERVATIONS ---
    vital = models.VitalObservation(
        patient_id=patient_id,
        encounter_id=encounter.id,
        heart_rate=72.0,
        systolic_bp=128.0,
        diastolic_bp=82.0,
        spo2=98.5,
        temperature_c=36.7,
        observed_at=datetime.now()
    )
    db_session.add(vital)
    db_session.commit()

    # --- 3. GRANT INTEROPERABILITY CONSENT ---
    # Log in as patient to grant consent
    pat_login = client.post("/token", data={"username": patient_username, "password": password})
    assert pat_login.status_code == 200
    pat_token = pat_login.json()["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    consent_res = client.post("/interop/consents", json={
        "purpose": "E2E Care Export",
        "recipient_type": "care_team"
    }, headers=pat_headers)
    assert consent_res.status_code in [200, 201]

    # --- 4. EXPORT AND VERIFY FHIR BUNDLE ---
    # Log in as doctor to query bundle
    doc_login = client.post("/token", data={"username": doctor_username, "password": password})
    assert doc_login.status_code == 200
    doc_token = doc_login.json()["access_token"]
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    # Fetch dynamic FHIR Bundle
    bundle_res = client.get(
        f"/interop/doctor/patients/{patient_id}/fhir-bundle",
        headers=doc_headers
    )
    assert bundle_res.status_code == 200
    bundle_data = bundle_res.json()["bundle"]
    
    assert bundle_data["resourceType"] == "Bundle"
    
    # Verify patient details are dynamically loaded from SQL EMR
    patient_entry = next(e for e in bundle_data["entry"] if e["resource"]["resourceType"] == "Patient")
    assert patient_entry["resource"]["name"][0]["text"] == "Alice Patient E2E"
    assert patient_entry["resource"]["birthDate"] == "1980-05-15"

    # Verify vital observations are dynamically mapped to FHIR R4 Observations
    obs_entry = next(e for e in bundle_data["entry"] if e["resource"]["resourceType"] == "Observation")
    assert obs_entry["resource"]["status"] == "final"
    components = obs_entry["resource"]["component"]
    systolic_comp = next(c for c in components if c["code"]["coding"][0]["code"] == "8480-6")
    assert systolic_comp["valueQuantity"]["value"] == 128.0

    # --- 5. RUN REAL TEE-ATTESTED ML INFERENCE ---
    # Temporarily remove TESTING env var to trigger real model initialization & execution
    original_testing = os.environ.get("TESTING")
    if "TESTING" in os.environ:
        del os.environ["TESTING"]

    try:
        # Re-initialize model service to load actual models from disk and sync globals
        from backend.prediction import initialize_models
        import backend.prediction as pred
        model_service._initialized = False
        initialize_models()
        # Set prediction.diabetes_model to None to force _run_model_prediction_scaled
        # to execute the unmocked _onnx_execution/_pkl_execution paths rather than
        # the pytest-specific _test_execution.
        pred.diabetes_model = None

        # Set headers for patient
        prediction_res = client.post(
            "/predict/diabetes",
            json={
                "gender": 0,
                "age": 45.0,
                "hypertension": 0,
                "heart_disease": 0,
                "smoking_history": 3,
                "bmi": 27.5,
                "high_chol": 1,
                "physical_activity": 1,
                "general_health": 2
            },
            headers=pat_headers
        )
        assert prediction_res.status_code == 200
        pred_json = prediction_res.json()
        
        # Verify prediction outcomes
        assert pred_json["prediction"] in ["Diabetes Detected", "Healthy Profile", "Low Risk", "High Risk"]
        assert "confidence" in pred_json
        
        # Verify that TEE enclave attestation was run and registered the model hash
        assert "diabetes" in TRUSTED_MODEL_HASHES
        assert len(TRUSTED_MODEL_HASHES["diabetes"]) == 64  # valid SHA-256 hex string

    finally:
        if original_license is not None:
            os.environ["LICENSE_KEY"] = original_license
        else:
            os.environ.pop("LICENSE_KEY", None)
        # Restore test harness state
        if original_testing is not None:
            os.environ["TESTING"] = original_testing
        from backend.prediction import initialize_models
        model_service._initialized = False
        initialize_models()
