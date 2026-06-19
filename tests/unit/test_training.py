from unittest.mock import mock_open, patch, MagicMock
import numpy as np
import pandas as pd

# Import the training functions
from backend.train_diabetes import train_diabetes_model
from backend.train_heart import train_heart_model
from backend.train_liver import train_liver_model


def test_train_diabetes():
    with patch("pandas.read_parquet") as mock_read, \
         patch("backend.train_diabetes.os.path.exists", return_value=True), \
         patch("backend.train_diabetes.pickle.dump") as mock_pickle, \
         patch("sklearn.ensemble.VotingClassifier") as mock_vc, \
         patch("backend.train_diabetes.open", mock_open()):

        df = pd.DataFrame({
            "gender": [1, 0, 1] * 10,
            "age_bucket": [5] * 30,
            "hypertension": [0] * 30,
            "high_chol": [0] * 30,
            "bmi": [25.0] * 30,
            "smoking_history": [0] * 30,
            "heart_disease": [0] * 30,
            "physical_activity": [1] * 30,
            "general_health": [3] * 30,
            "diabetes": [0] * 30
        })
        mock_read.return_value = df

        mock_model = MagicMock()
        mock_model.predict.side_effect = lambda x: np.zeros(len(x))
        mock_model.predict_proba.side_effect = lambda x: np.column_stack([np.ones(len(x)), np.zeros(len(x))])
        mock_model.feature_importances_ = np.zeros(9)
        mock_vc.return_value = mock_model

        # Run
        train_diabetes_model()

        # Verify
        assert mock_read.called
        assert mock_model.fit.called
        assert mock_pickle.called


def test_train_heart():
    with patch("pandas.read_parquet") as mock_read, \
         patch("backend.train_heart.os.path.exists", return_value=True), \
         patch("backend.train_heart.pickle.dump") as mock_pickle, \
         patch("sklearn.ensemble.VotingClassifier") as mock_vc, \
         patch("backend.train_heart.open", mock_open()):

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

        mock_model = MagicMock()
        mock_model.predict.side_effect = lambda x: np.zeros(len(x))
        mock_model.predict_proba.side_effect = lambda x: np.column_stack([np.ones(len(x)), np.zeros(len(x))])
        mock_model.feature_importances_ = np.zeros(13)
        mock_vc.return_value = mock_model

        train_heart_model()

        assert mock_model.fit.called
        assert mock_pickle.called


def test_train_liver():
    with patch("pandas.read_parquet") as mock_read, \
         patch("backend.train_liver.os.path.exists", return_value=True), \
         patch("backend.train_liver.pickle.dump") as mock_pickle, \
         patch("sklearn.ensemble.VotingClassifier") as mock_vc, \
         patch("backend.train_liver.open", mock_open()):

        # Dataset needs mixed classes 1 and 2
        df = pd.DataFrame({
            "Age": [40] * 30,
            "Gender": [0, 1] * 15,
            "Total_Bilirubin": [0.8] * 30,
            "Direct_Bilirubin": [0.2] * 30,
            "Alkaline_Phosphotase": [180] * 30,
            "Alamine_Aminotransferase": [20] * 30,
            "Aspartate_Aminotransferase": [25] * 30,
            "Total_Proteins": [6.5] * 30,
            "Albumin": [3.5] * 30,
            "Albumin_and_Globulin_Ratio": [1.0] * 30,
            "target": [0, 1] * 15
        })
        mock_read.return_value = df

        mock_model = MagicMock()
        mock_model.predict.side_effect = lambda x: np.zeros(len(x))
        mock_model.predict_proba.side_effect = lambda x: np.column_stack([np.ones(len(x)), np.zeros(len(x))])
        mock_model.feature_importances_ = np.zeros(10)
        mock_vc.return_value = mock_model

        train_liver_model()

        assert mock_read.called
        assert mock_model.fit.called
        assert mock_pickle.called
