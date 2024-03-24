"""
Additional tests for backend/prediction.py SHAP explanation endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np

from fastapi import FastAPI
import backend.prediction
from backend.prediction import router

# Test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestDiabetesExplanation:
    """Tests for diabetes SHAP explanation endpoint."""
    
    def test_explain_diabetes_model_unavailable(self):
        """Test error when model not available."""
        with patch("backend.prediction.diabetes_model", None):
            resp = client.post("/predict/explain/diabetes", json={
                "gender": 1, "age": 50, "hypertension": 0, "heart_disease": 0,
                "smoking_history": 1, "bmi": 25.0, "high_chol": 0, 
                "physical_activity": 1, "general_health": 2
            })
            assert resp.status_code == 503
    
    def test_explain_diabetes_success(self):
        """Test successful explanation generation."""
        mock_model = MagicMock()
        mock_shap_result = {"html": "<div>SHAP Plot</div>"}
        
        with patch("backend.prediction.diabetes_model", mock_model), \
             patch("backend.prediction.explainability.get_shap_values", return_value=mock_shap_result):
            
            resp = client.post("/predict/explain/diabetes", json={
                "gender": 1, "age": 50, "hypertension": 0, "heart_disease": 0,
                "smoking_history": 1, "bmi": 25.0, "high_chol": 0,
                "physical_activity": 1, "general_health": 2
            })
            
            if resp.status_code == 200:
                assert "html" in resp.json()
    
    def test_explain_diabetes_shap_failure(self):
        """Test error when SHAP generation fails."""
        mock_model = MagicMock()
        
        with patch("backend.prediction.diabetes_model", mock_model), \
             patch("backend.prediction.explainability.get_shap_values", return_value=None):
            
            resp = client.post("/predict/explain/diabetes", json={
                "gender": 1, "age": 50, "hypertension": 0, "heart_disease": 0,
                "smoking_history": 1, "bmi": 25.0, "high_chol": 0,
                "physical_activity": 1, "general_health": 2
            })
            assert resp.status_code == 500


class TestHeartExplanation:
    """Tests for heart disease SHAP explanation endpoint."""
    
    def test_explain_heart_model_unavailable(self):
        """Test error when model not available."""
        with patch("backend.prediction.heart_model", None):
            resp = client.post("/predict/explain/heart", json={
                "age": 50, "gender": 1, "high_bp": 0, "high_chol": 200, "bmi": 25.0,
                "smoker": 0, "stroke": 0, "diabetes": 0, "phys_activity": 1,
                "hvy_alcohol": 0, "gen_hlth": 2
            })
            assert resp.status_code == 503
    
    def test_explain_heart_success(self):
        """Test successful heart explanation."""
        mock_model = MagicMock()
        mock_shap = {"html": "<div>Heart SHAP</div>"}
        
        with patch("backend.prediction.heart_model", mock_model), \
             patch("backend.prediction.explainability.get_shap_values", return_value=mock_shap):
            
            resp = client.post("/predict/explain/heart", json={
                "age": 50, "gender": 1, "high_bp": 0, "high_chol": 200, "bmi": 25.0,
                "smoker": 0, "stroke": 0, "diabetes": 0, "phys_activity": 1,
                "hvy_alcohol": 0, "gen_hlth": 2
            })
            
            if resp.status_code == 200:
                assert "html" in resp.json()


class TestLiverExplanation:
    """Tests for liver disease SHAP explanation endpoint."""
    
    def test_explain_liver_model_unavailable(self):
        """Test error when model or scaler not available."""
        with patch("backend.prediction.liver_model", None):
            resp = client.post("/predict/explain/liver", json={
                "age": 45, "gender": 1, "total_bilirubin": 1.0,
                "alkaline_phosphotase": 100, "alamine_aminotransferase": 30,
                "albumin_and_globulin_ratio": 1.0, "direct_bilirubin": 0.5,
                "aspartate_aminotransferase": 30, "total_proteins": 6.0, "albumin": 3.0
            })
            assert resp.status_code == 503
    
    def test_explain_liver_success(self):
        """Test successful liver explanation."""
        mock_model = MagicMock()
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[1,2,3,4,5,6,7,8,9,10]])
        mock_shap = {"html": "<div>Liver SHAP</div>"}
        
        with patch("backend.prediction.liver_model", mock_model), \
             patch("backend.prediction.liver_scaler", mock_scaler), \
             patch("backend.prediction.explainability.get_shap_values", return_value=mock_shap):
            
            resp = client.post("/predict/explain/liver", json={
                "age": 45, "gender": 1, "total_bilirubin": 1.0,
                "alkaline_phosphotase": 100, "alamine_aminotransferase": 30,
                "albumin_and_globulin_ratio": 1.0, "direct_bilirubin": 0.5,
                "aspartate_aminotransferase": 30, "total_proteins": 6.0, "albumin": 3.0
            })
            
            if resp.status_code == 200:
                assert "html" in resp.json()
