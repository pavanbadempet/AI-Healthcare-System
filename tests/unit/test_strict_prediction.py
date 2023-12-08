import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import numpy as np

# Import app to get router, but we might need to patch dependencies
# backend.main includes prediction router.
# Let's import prediction module directly to patch globals.
from fastapi import FastAPI
import backend.prediction
from backend.prediction import router

# Wrap router in App to avoid middleware scope issues
app = FastAPI()
app.include_router(router)

client = TestClient(app)

# --- Diabetes Tests ---

def test_predict_diabetes_success():
    # Setup Mock
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([1]) # High Risk
    
    with patch("backend.prediction.diabetes_model", mock_model):
        resp = client.post("/predict/diabetes", json={
            "gender": 1, "age": 50, "hypertension": 0, "heart_disease": 0,
            "smoking_history": 1, "bmi": 25.0, "high_chol": 0, "physical_activity": 1, "general_health": 2
        })
        assert resp.status_code == 200
        assert resp.json()["prediction"] == "High Risk"

def test_predict_diabetes_model_unavailable():
    # Force model to be None to hit 503
    with patch("backend.prediction.diabetes_model", None):
        resp = client.post("/predict/diabetes", json={
            "gender": 1, "age": 50, "hypertension": 0, "heart_disease": 0,
            "smoking_history": 1, "bmi": 25.0, "high_chol": 0, "physical_activity": 1, "general_health": 2
        })
        assert resp.status_code == 503
        assert "not available" in resp.json()["detail"]

def test_predict_diabetes_exception():
    # Force exception during predict
    mock_model = MagicMock()
    mock_model.predict.side_effect = Exception("Model Failure")
    
    with patch("backend.prediction.diabetes_model", mock_model):
        resp = client.post("/predict/diabetes", json={
            "gender": 1, "age": 50, "hypertension": 0, "heart_disease": 0,
            "smoking_history": 1, "bmi": 25.0, "high_chol": 0, "physical_activity": 1, "general_health": 2
        })
        assert resp.status_code == 500
        assert "Model Failure" in resp.json()["detail"]

# --- Heart Tests ---
    
def test_predict_heart_success():
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([1]) # Disease
    
    with patch("backend.prediction.heart_model", mock_model):
        resp = client.post("/predict/heart", json={
            "age": 50, "gender": 1, "high_bp": 0, "high_chol": 200, "bmi": 25.0, 
            "smoker": 0, "stroke": 0, "diabetes": 0, "phys_activity": 1, "hvy_alcohol": 0, "gen_hlth": 2
        })
        assert resp.status_code == 200
        assert resp.json()["prediction"] == "Heart Disease Detected"

def test_predict_heart_model_unavailable():
    with patch("backend.prediction.heart_model", None):
        resp = client.post("/predict/heart", json={
            "age": 50, "gender": 1, "high_bp": 0, "high_chol": 200, "bmi": 25.0, 
            "smoker": 0, "stroke": 0, "diabetes": 0, "phys_activity": 1, "hvy_alcohol": 0, "gen_hlth": 2
        })
        assert resp.status_code == 503

def test_predict_heart_exception():
    mock_model = MagicMock()
    mock_model.predict.side_effect = Exception("Boom")
    
    with patch("backend.prediction.heart_model", mock_model):
        resp = client.post("/predict/heart", json={
            "age": 50, "gender": 1, "high_bp": 0, "high_chol": 200, "bmi": 25.0, 
            "smoker": 0, "stroke": 0, "diabetes": 0, "phys_activity": 1, "hvy_alcohol": 0, "gen_hlth": 2
        })
        assert resp.status_code == 500

# --- Liver Tests ---

def test_predict_liver_success():
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([0]) # Healthy
    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = np.array([[1,2,3,4,5,6]])
    
    with patch("backend.prediction.liver_model", mock_model), \
         patch("backend.prediction.liver_scaler", mock_scaler):
        
        resp = client.post("/predict/liver", json={
            "age": 45, "gender": 1, "total_bilirubin": 1.0,
            "alkaline_phosphotase": 100, "alamine_aminotransferase": 30,
            "albumin_and_globulin_ratio": 1.0, "direct_bilirubin": 0.5,
            "aspartate_aminotransferase": 30, "total_proteins": 6.0, "albumin": 3.0
        })
        assert resp.status_code == 200
        assert resp.json()["prediction"] == "Healthy Liver"

def test_predict_liver_unavailable():
    # Test both model and scaler missing
    with patch("backend.prediction.liver_model", None):
        resp = client.post("/predict/liver", json={
            "age": 45, "gender": 1, "total_bilirubin": 1.0,
            "alkaline_phosphotase": 100, "alamine_aminotransferase": 30,
            "albumin_and_globulin_ratio": 1.0, "direct_bilirubin": 0.5,
            "aspartate_aminotransferase": 30, "total_proteins": 6.0, "albumin": 3.0
        })
        assert resp.status_code == 503

def test_predict_liver_exception():
    mock_model = MagicMock()
    mock_model.predict.side_effect = Exception("Liver Fail")
    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = np.array([[1,2,3,4,5,6]])
    
    with patch("backend.prediction.liver_model", mock_model), \
         patch("backend.prediction.liver_scaler", mock_scaler):
         
        resp = client.post("/predict/liver", json={
            "age": 45, "gender": 1, "total_bilirubin": 1.0,
            "alkaline_phosphotase": 100, "alamine_aminotransferase": 30,
            "albumin_and_globulin_ratio": 1.0, "direct_bilirubin": 0.5,
            "aspartate_aminotransferase": 30, "total_proteins": 6.0, "albumin": 3.0
        })
        assert resp.status_code == 500
        assert "Liver Fail" in resp.json()["detail"]

# --- Import Error Test ---
# This is tricky because it runs at import time. We use reload.
import importlib
import builtins

def test_model_loading_failure():
    # Patch open to fail, forcing exception block
    with patch("builtins.open", side_effect=FileNotFoundError("Mock File Missing")):
        # Reload module
        importlib.reload(backend.prediction)
        
        # Check globals are DummyModel instances (not None)
        assert backend.prediction.diabetes_model is not None
        assert type(backend.prediction.diabetes_model).__name__ == "DummyModel"
        assert backend.prediction.heart_model is not None
        assert type(backend.prediction.heart_model).__name__ == "DummyModel"
        
    # Restore module (reload again without patch) to fix state for other tests?
    # Actually, other tests rely on patching the GLOBAL variable, so if it is None, strict patching works fine.
    # But let's try to restore just in case.
    try:
        importlib.reload(backend.prediction)
    except:
        pass # If local files are missing, it stays None, which is fine.
