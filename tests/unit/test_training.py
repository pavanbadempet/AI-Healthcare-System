import pytest
from unittest.mock import MagicMock, patch, mock_open
import pandas as pd
import numpy as np

# Import the training functions
from backend.train_diabetes import train_diabetes_model
from backend.train_heart import train_heart_model
from backend.train_liver import train_liver_model

def test_train_diabetes():
    with patch("pandas.read_parquet") as mock_read, \
         patch("backend.train_diabetes.os.path.exists", return_value=True), \
         patch("backend.train_diabetes.pickle.dump") as mock_pickle, \
         patch("xgboost.XGBClassifier") as mock_xgb:
        
        # Setup Mock Data
        df = pd.DataFrame({
            "gender": ["Male", "Female", "Other"] * 10,
            "age": [30.0] * 30,
            "hypertension": [0] * 30,
            "heart_disease": [0] * 30,
            "smoking_history": ["never"] * 30,
            "bmi": [25.0] * 30,
            "HbA1c_level": [5.5] * 30,
            "blood_glucose_level": [100] * 30,
            "diabetes": [0] * 30
        })
        mock_read.return_value = df
        
        # Mock Predict to return a list (not a Mock)
        mock_xgb.return_value.predict.side_effect = lambda x: [0] * len(x)
        
        # Run
        train_diabetes_model()
        
        # Verify
        assert mock_read.called
        assert mock_xgb.return_value.fit.called
        assert mock_pickle.called

def test_train_heart():
    with patch("pandas.read_parquet") as mock_read, \
         patch("backend.train_heart.os.path.exists", return_value=True), \
         patch("backend.train_heart.pickle.dump") as mock_pickle, \
         patch("xgboost.XGBClassifier") as mock_xgb:
        
        df = pd.DataFrame({
            "age": [50] * 30,
            "sex": [1] * 30,
            "cp": [0] * 30,
            "trestbps": [120] * 30,
            "chol": [200] * 30,
            "fbs": [0] * 30,
            "restecg": [0] * 30,
            "thalach": [150] * 30,
            "exang": [0] * 30,
            "oldpeak": [0.0] * 30,
            "slope": [1] * 30,
            "ca": [0] * 30,
            "thal": [2] * 30,
            "target": [0] * 30
        })
        mock_read.return_value = df
        mock_xgb.return_value.predict.side_effect = lambda x: [0] * len(x)
        
        train_heart_model()
        
        assert mock_read.called
        assert mock_xgb.return_value.fit.called
        assert mock_pickle.called

def test_train_liver():
    with patch("pandas.read_parquet") as mock_read, \
         patch("backend.train_liver.os.path.exists", return_value=True), \
         patch("backend.train_liver.pickle.dump") as mock_pickle, \
         patch("xgboost.XGBClassifier") as mock_xgb, \
         patch("builtins.open", mock_open()):
        
        # Dataset needs mixed classes 1 and 2
        df = pd.DataFrame({
            "Age": [40] * 30,
            "Gender": ["Male", "Female"] * 15,
            "Total_Bilirubin": [0.8] * 30,
            "Direct_Bilirubin": [0.2] * 30,
            "Alkaline_Phosphotase": [180] * 30,
            "Alamine_Aminotransferase": [20] * 30,
            "Aspartate_Aminotransferase": [25] * 30,
            "Total_Protiens": [6.5] * 30,
            "Albumin": [3.5] * 30,
            "Albumin_and_Globulin_Ratio": [1.0] * 30,
            "target": [0, 1] * 15
        })
        # Note: I am fixing the mocked column name to 'target' to match train_liver.py logic.
        mock_read.return_value = df
        mock_xgb.return_value.predict.side_effect = lambda x: [1] * len(x)
        
        train_liver_model()
        
        assert mock_read.called
        assert mock_xgb.return_value.fit.called
        assert mock_pickle.called
