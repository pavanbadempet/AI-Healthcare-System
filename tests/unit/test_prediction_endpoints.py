import pytest
from unittest.mock import patch
from backend.main import app
from backend.auth import get_current_user
from backend.models.auth import User
from backend.models.clinical import VitalObservation

def mock_get_current_user():
    return User(id=1, email="doctor@example.com", role="doctor")

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture(autouse=True)
def mock_prediction_dependencies():
    with patch("backend.prediction._prediction_patient") as mock_patient, \
         patch("backend.prediction._ensure_prediction_review_access") as mock_access, \
         patch("backend.prediction.users_share_facility_context") as mock_facility, \
         patch("backend.prediction._run_model_prediction_scaled") as mock_predict, \
         patch("backend.prediction._run_diabetes_proba") as mock_diab_proba, \
         patch("backend.prediction._run_heart_proba") as mock_heart_proba, \
         patch("backend.prediction._get_triage_recommendation") as mock_triage, \
         patch("backend.prediction._get_top_risk_factors") as mock_risk:
         
        mock_patient.return_value.id = 123
        mock_patient.return_value.gender = "male"
        mock_patient.return_value.dob = "1980-01-01"
        mock_facility.return_value = True
        mock_predict.return_value = (1, 85.0, "High Risk", [0.2, 0.8])
        mock_triage.return_value = "Follow up"
        mock_risk.return_value = [{"feature": "feature1", "impact": 0.5}]
        yield

def test_predict_kidney(client):
    payload = {
        "patient_id": 123,
        "age": 45,
        "blood_pressure": 120,
        "specific_gravity": 1.020,
        "albumin": 0,
        "sugar": 0,
        "red_blood_cells": 1,
        "pus_cell": 1,
        "pus_cell_clumps": 0,
        "bacteria": 0,
        "blood_glucose_random": 150.0,
        "blood_urea": 40.0,
        "serum_creatinine": 1.0,
        "sodium": 140.0,
        "potassium": 4.5,
        "hemoglobin": 14.0,
        "packed_cell_volume": 42.0,
        "white_blood_cell_count": 8000.0,
        "red_blood_cell_count": 5.0,
        "hypertension": 0,
        "diabetes_mellitus": 0,
        "coronary_artery_disease": 0,
        "appetite": 1,
        "pedal_edema": 0,
        "anemia": 0
    }
    response = client.post("/v1/predict/kidney", json=payload)
    assert response.status_code == 200

def test_predict_lungs(client):
    payload = {
        "patient_id": 123,
        "age": 45,
        "gender": 1,
        "smoking": 1,
        "yellow_fingers": 0,
        "anxiety": 0,
        "peer_pressure": 0,
        "chronic_disease": 0,
        "fatigue": 0,
        "allergy": 0,
        "wheezing": 0,
        "alcohol_consuming": 0,
        "coughing": 0,
        "shortness_of_breath": 0,
        "swallowing_difficulty": 0,
        "chest_pain": 1
    }
    response = client.post("/v1/predict/lungs", json=payload)
    assert response.status_code == 200

def test_predict_diabetes(client):
    payload = {
        "patient_id": 123,
        "pregnancies": 0,
        "glucose": 100,
        "blood_pressure": 120,
        "skin_thickness": 20,
        "insulin": 80,
        "bmi": 25.0,
        "diabetes_pedigree_function": 0.5,
        "age": 45
    }
    response = client.post("/v1/predict/diabetes", json=payload)
    assert response.status_code == 200

def test_predict_heart(client):
    payload = {
        "patient_id": 123,
        "age": 45,
        "sex": 1,
        "cp": 1,
        "trestbps": 120,
        "chol": 200,
        "fbs": 0,
        "restecg": 1,
        "thalach": 150,
        "exang": 0,
        "oldpeak": 1.0,
        "slope": 1,
        "ca": 0,
        "thal": 2
    }
    response = client.post("/v1/predict/heart", json=payload)
    assert response.status_code == 200

def test_predict_liver(client):
    payload = {
        "patient_id": 123,
        "age": 45,
        "gender": 1,
        "total_bilirubin": 1.0,
        "direct_bilirubin": 0.3,
        "alkaline_phosphotase": 100,
        "alamine_aminotransferase": 30,
        "aspartate_aminotransferase": 30,
        "total_proteins": 6.5,
        "albumin": 3.5,
        "albumin_and_globulin_ratio": 1.0
    }
    response = client.post("/v1/predict/liver", json=payload)
    assert response.status_code == 200

def test_predict_stroke(client):
    payload = {
        "patient_id": 123,
        "gender": 1,
        "age": 45,
        "hypertension": 0,
        "heart_disease": 0,
        "ever_married": 1,
        "work_type": 1,
        "residence_type": 1,
        "avg_glucose_level": 100.0,
        "bmi": 25.0,
        "smoking_status": 0
    }
    response = client.post("/v1/predict/stroke", json=payload)
    assert response.status_code == 200

def test_predict_multi_organ(client):
    payload = {
        "patient_id": 123,
        "age": 45,
        "gender": 1,
        "bmi": 25.0,
        "blood_pressure_systolic": 120.0,
        "blood_pressure_diastolic": 80.0,
        "heart_rate": 72.0,
        "respiratory_rate": 14.0,
        "body_temperature": 36.8,
        "blood_glucose": 100.0,
        "cholesterol_total": 200.0,
        "hdl_cholesterol": 50.0,
        "ldl_cholesterol": 120.0,
        "triglycerides": 150.0,
        "smoking_status": 0,
        "alcohol_consumption": 0,
        "physical_activity": 1
    }
    response = client.post("/v1/predict/multi-organ", json=payload)
    assert response.status_code == 200

def test_predict_organ_health(client, db_session):
    # Insert a patient and vital observation
    patient = User(id=123, email="patient@example.com", role="patient")
    db_session.add(patient)
    db_session.commit()
    
    vital = VitalObservation(
        patient_id=123,
        heart_rate=75.0,
        systolic_bp=120.0,
        diastolic_bp=80.0,
        spo2=98.0,
        temperature_c=36.5,
        respiratory_rate=14.0
    )
    db_session.add(vital)
    db_session.commit()
    
    response = client.get("/v1/predict/organ_health/123")
    assert response.status_code == 200
