from unittest.mock import MagicMock
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.model_service import model_service
from backend.prediction import initialize_models

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    app.dependency_overrides[get_db] = override_get_db
    initialize_models()
    with TestClient(app, base_url="http://127.0.0.1") as c:
        yield c
    app.dependency_overrides.clear()

def get_auth_headers(client, username="preduser"):
    client.post("/signup", json={
        "username": username,
        "password": "SotaPassword123!",
        "email": f"{username}@test.com",
        "full_name": "Pred Test User",
        "dob": "1990-01-01",
    })
    r = client.post("/token", data={"username": username, "password": "SotaPassword123!"})
    if r.status_code != 200:
        return {}
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def mock_predict_for_model(model_name):
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([1])
    mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])
    model_service._entries[model_name].model = mock_model
    setattr(model_service._entries[model_name], "model_version", "1.0.0-test")
    setattr(model_service._entries[model_name], "training_timestamp", "2026-06-18T12:00:00")
    
    from backend import prediction as _pred
    setattr(_pred, f"{model_name}_model", mock_model)

def test_diabetes_prediction(client, db_session):
    mock_predict_for_model("diabetes")
    payload = {
        "gender": 1, "age": 45, "hypertension": 1, "heart_disease": 0,
        "smoking_history": 0, "bmi": 28.5, "high_chol": 1, 
        "physical_activity": 1, "general_health": 3
    }
    response = client.post("/predict/diabetes", json=payload, headers=get_auth_headers(client, "diabuser"))
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data

def test_heart_prediction(client, db_session):
    mock_predict_for_model("heart")
    payload = {
        "age": 55, "sex": 1, "cp": 3, "trestbps": 140, "chol": 240,
        "fbs": 1, "restecg": 0, "thalach": 150, "exang": 0, "oldpeak": 1.5,
        "slope": 2, "ca": 0, "thal": 2, "hdl": 45, "smoker": 1, "hyp_treatment": 0
    }
    response = client.post("/predict/heart", json=payload, headers=get_auth_headers(client, "heartuser"))
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data

def test_lung_prediction(client, db_session):
    mock_predict_for_model("lungs")
    payload = {
        "gender": 0, "age": 60, "smoking": 2, "yellow_fingers": 2, "anxiety": 2,
        "peer_pressure": 1, "chronic_disease": 1, "fatigue": 2, "allergy": 1,
        "wheezing": 2, "alcohol": 1, "coughing": 2, "shortness_of_breath": 2,
        "swallowing_difficulty": 1, "chest_pain": 2
    }
    response = client.post("/predict/lungs", json=payload, headers=get_auth_headers(client, "lunguser"))
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data

def test_liver_prediction(client, db_session):
    mock_predict_for_model("liver")
    payload = {
        "age": 50, "gender": 1, "total_bilirubin": 1.2, "direct_bilirubin": 0.4,
        "alkaline_phosphotase": 150, "alamine_aminotransferase": 40,
        "aspartate_aminotransferase": 45, "total_proteins": 6.8, "albumin": 3.5,
        "albumin_and_globulin_ratio": 1.0, "platelets": 200
    }
    response = client.post("/predict/liver", json=payload, headers=get_auth_headers(client, "liveruser"))
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data

def test_stroke_prediction(client, db_session):
    mock_predict_for_model("stroke")
    payload = {
        "gender": 1, "age": 65, "hypertension": 1, "heart_disease": 1,
        "smoking": 1, "bmi": 30.5, "glucose": 150.0
    }
    response = client.post("/predict/stroke", json=payload, headers=get_auth_headers(client, "strokeuser"))
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data

def test_multi_organ_prediction(client, db_session):
    mock_predict_for_model("diabetes")
    mock_predict_for_model("heart")
    mock_predict_for_model("lungs")
    mock_predict_for_model("liver")
    mock_predict_for_model("stroke")
    mock_predict_for_model("kidney")
    
    payload = {
        "gender": 1, "age": 55, "smoking": 1, "physical_activity": 1,
        "alcohol": 1, "general_health": 3, "bmi": 28.5, "glucose": 150.0,
        "hba1c": 6.5, "hypertension": 1, "heart_disease": 0, "cp": 3,
        "trestbps": 140.0, "chol": 240.0, "fbs": 1, "restecg": 0,
        "thalach": 150.0, "exang": 0, "oldpeak": 1.5, "slope": 2,
        "ca": 0, "thal": 2, "hdl": 45.0, "hyp_treatment": 0,
        "total_bilirubin": 1.2, "direct_bilirubin": 0.4,
        "alkaline_phosphotase": 150.0, "alamine_aminotransferase": 40.0,
        "aspartate_aminotransferase": 45.0, "total_proteins": 6.8, "albumin": 3.5,
        "albumin_and_globulin_ratio": 1.0, "platelets": 200.0, "bp": 130.0,
        "sg": 1.020, "al": 1.0, "su": 0.0, "rbc": 0, "pc": 1, "pcc": 0,
        "ba": 0, "bgr": 120.0, "bu": 40.0, "sc": 1.2, "sod": 138.0,
        "pot": 4.5, "hemo": 15.0, "pcv": 45.0, "wc": 8000.0, "rc": 5.0,
        "htn": 1, "dm": 1, "cad": 0, "appet": 0, "pe": 0, "ane": 0,
        "yellow_fingers": 2, "anxiety": 2, "peer_pressure": 1,
        "chronic_disease": 1, "fatigue": 2, "allergy": 1, "wheezing": 2,
        "coughing": 2, "shortness_of_breath": 2, "swallowing_difficulty": 1,
        "chest_pain": 2
    }
    
    response = client.post("/predict/multi-organ", json=payload, headers=get_auth_headers(client, "multiuser"))
    assert response.status_code == 200
    data = response.json()
    assert "health_index" in data
    assert "organ_risks" in data
