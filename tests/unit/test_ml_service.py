"""
Tests for backend/ml_service.py to increase coverage.
Tests the legacy MLService class methods.
"""
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from backend.ml_service import MLService, ml_service


class TestMLServiceDiabetes:
    """Tests for MLService.predict_diabetes method."""
    
    def test_predict_diabetes_success(self):
        """Test successful diabetes prediction via MLService."""
        mock_result = {"prediction": "High Risk", "raw": 1}
        
        with patch("backend.ml_service.prediction.predict_diabetes", return_value=mock_result):
            service = MLService()
            result = service.predict_diabetes(
                gender="male",
                age=50,
                hypertension=1,
                heart_disease=0,
                smoking_history="current",
                bmi=28.5,
                hba1c_level=6.5,
                blood_glucose_level=150
            )
            
            assert result == "High Risk"
    
    def test_predict_diabetes_female(self):
        """Test diabetes prediction for female."""
        mock_result = {"prediction": "Low Risk", "raw": 0}
        
        with patch("backend.ml_service.prediction.predict_diabetes", return_value=mock_result):
            service = MLService()
            result = service.predict_diabetes(
                gender="female",
                age=35,
                hypertension=0,
                heart_disease=0,
                smoking_history="never",
                bmi=24.0,
                hba1c_level=5.5,
                blood_glucose_level=100
            )
            
            assert result == "Low Risk"
    
    def test_predict_diabetes_smoking_mapping(self):
        """Test all smoking history mappings."""
        mock_result = {"prediction": "Low Risk", "raw": 0}
        
        with patch("backend.ml_service.prediction.predict_diabetes", return_value=mock_result):
            service = MLService()
            
            # Test different smoking values
            for smoking in ["never", "current", "former", "ever", "not current", "unknown"]:
                result = service.predict_diabetes(
                    gender="male", age=40, hypertension=0, heart_disease=0,
                    smoking_history=smoking, bmi=25.0, hba1c_level=5.0, blood_glucose_level=100
                )
                assert result is not None
    
    def test_predict_diabetes_exception(self):
        """Test error handling in diabetes prediction."""
        with patch("backend.ml_service.prediction.predict_diabetes", side_effect=Exception("Model error")):
            service = MLService()
            result = service.predict_diabetes(
                gender="male", age=50, hypertension=1, heart_disease=0,
                smoking_history="never", bmi=28.0, hba1c_level=7.0, blood_glucose_level=200
            )
            
            assert "Error" in result


class TestMLServiceHeart:
    """Tests for MLService.predict_heart_disease method."""
    
    def test_predict_heart_success(self):
        """Test successful heart prediction."""
        mock_result = {"prediction": "Heart Disease Detected", "raw": 1}
        
        with patch("backend.ml_service.prediction.predict_heart", return_value=mock_result):
            service = MLService()
            result = service.predict_heart_disease(
                age=60, gender="male", cp=2, trestbps=140, chol=250,
                fbs=1, restecg=0, thalach=150, exang=0, oldpeak=1.5,
                slope=1, ca=0, thal=2
            )
            
            assert result == "Heart Disease Detected"
    
    def test_predict_heart_high_bp_threshold(self):
        """Test high BP threshold detection."""
        mock_result = {"prediction": "Healthy Heart", "raw": 0}
        
        with patch("backend.ml_service.prediction.predict_heart", return_value=mock_result) as mock_pred:
            service = MLService()
            
            # Test with high BP (>130)
            service.predict_heart_disease(
                age=50, gender="male", cp=0, trestbps=135, chol=180,
                fbs=0, restecg=0, thalach=160, exang=0, oldpeak=0,
                slope=0, ca=0, thal=1
            )
            
            # Verify high_bp was set to 1
            call_args = mock_pred.call_args[0][0]
            assert call_args.high_bp == 1
    
    def test_predict_heart_exception(self):
        """Test error handling in heart prediction."""
        with patch("backend.ml_service.prediction.predict_heart", side_effect=Exception("Heart model error")):
            service = MLService()
            result = service.predict_heart_disease(
                age=60, gender="male", cp=2, trestbps=140, chol=250,
                fbs=1, restecg=0, thalach=150, exang=0, oldpeak=1.5,
                slope=1, ca=0, thal=2
            )
            
            assert "Error" in result


class TestMLServiceLiver:
    """Tests for MLService.predict_liver_disease method."""
    
    def test_predict_liver_success(self):
        """Test successful liver prediction."""
        mock_result = {"prediction": "Healthy Liver", "raw": 0}
        
        with patch("backend.ml_service.prediction.predict_liver", return_value=mock_result):
            service = MLService()
            result = service.predict_liver_disease(
                age=45, gender="male", total_bilirubin=0.8,
                alkaline_phosphotase=150, alamine_aminotransferase=25,
                albumin_globulin_ratio=1.2
            )
            
            assert result == "Healthy Liver"
    
    def test_predict_liver_female(self):
        """Test liver prediction for female."""
        mock_result = {"prediction": "Liver Disease", "raw": 1}
        
        with patch("backend.ml_service.prediction.predict_liver", return_value=mock_result):
            service = MLService()
            result = service.predict_liver_disease(
                age=55, gender="female", total_bilirubin=2.5,
                alkaline_phosphotase=300, alamine_aminotransferase=80,
                albumin_globulin_ratio=0.7
            )
            
            assert result == "Liver Disease"
    
    def test_predict_liver_exception(self):
        """Test error handling in liver prediction."""
        with patch("backend.ml_service.prediction.predict_liver", side_effect=Exception("Liver model error")):
            service = MLService()
            result = service.predict_liver_disease(
                age=50, gender="male", total_bilirubin=1.0,
                alkaline_phosphotase=200, alamine_aminotransferase=40,
                albumin_globulin_ratio=1.0
            )
            
            assert "Error" in result


class TestMLServiceSingleton:
    """Tests for the module-level ml_service singleton."""
    
    def test_singleton_exists(self):
        """Test that ml_service singleton is created."""
        assert ml_service is not None
        assert isinstance(ml_service, MLService)
