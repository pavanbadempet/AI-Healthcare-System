import importlib.util
from unittest.mock import MagicMock, mock_open, patch

import numpy as np
import pandas as pd
import pytest

has_catboost = importlib.util.find_spec("catboost") is not None
has_lightgbm = importlib.util.find_spec("lightgbm") is not None


@pytest.mark.skipif(not has_catboost, reason="CatBoost is not installed")
def test_train_diabetes():
    from scripts.training.train_diabetes import train_diabetes_model
    with (
        patch("pandas.read_parquet") as mock_read,
        patch("scripts.training.train_diabetes.os.path.exists", return_value=True),
        patch("scripts.training.train_diabetes.pickle.dump") as mock_pickle,
        patch("sklearn.ensemble.VotingClassifier") as mock_vc,
        patch("scripts.training.train_diabetes.open", mock_open()),
    ):
        df = pd.DataFrame(
            {
                "gender": [1, 0, 1] * 10,
                "age_bucket": [5] * 30,
                "hypertension": [0] * 30,
                "high_chol": [0] * 30,
                "bmi": [25.0] * 30,
                "smoking_history": [0] * 30,
                "heart_disease": [0] * 30,
                "physical_activity": [1] * 30,
                "general_health": [3] * 30,
                "diabetes": [0, 1] * 15,
            }
        )
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


@pytest.mark.skipif(not has_catboost, reason="CatBoost is not installed")
def test_train_heart():
    from scripts.training.train_heart import train_heart_model
    with (
        patch("pandas.read_parquet") as mock_read,
        patch("scripts.training.train_heart.os.path.exists", return_value=True),
        patch("scripts.training.train_heart.pickle.dump") as mock_pickle,
        patch("sklearn.ensemble.VotingClassifier") as mock_vc,
        patch("scripts.training.train_heart.open", mock_open()),
    ):
        df = pd.DataFrame(
            {
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
                "target": [0, 1] * 15,
            }
        )
        mock_read.return_value = df

        mock_model = MagicMock()
        mock_model.predict.side_effect = lambda x: np.zeros(len(x))
        mock_model.predict_proba.side_effect = lambda x: np.column_stack([np.ones(len(x)), np.zeros(len(x))])
        mock_model.feature_importances_ = np.zeros(13)
        mock_vc.return_value = mock_model

        train_heart_model()

        assert mock_model.fit.called
        assert mock_pickle.called


@pytest.mark.skipif(not has_lightgbm, reason="LightGBM is not installed")
def test_train_liver():
    from scripts.training.train_liver import train_liver_model
    with (
        patch("pandas.read_parquet") as mock_read,
        patch("scripts.training.train_liver.os.path.exists", return_value=True),
        patch("scripts.training.train_liver.pickle.dump") as mock_pickle,
        patch("sklearn.ensemble.VotingClassifier") as mock_vc,
        patch("scripts.training.train_liver.open", mock_open()),
    ):
        # Dataset needs mixed classes 1 and 2
        df = pd.DataFrame(
            {
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
                "target": [0, 1] * 15,
            }
        )
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
