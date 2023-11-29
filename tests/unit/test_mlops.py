import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import sys
import os

# Ensure training_pipeline is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from training_pipeline.train import train_model

def test_train_pipeline():
    with patch("training_pipeline.train.mlflow") as mock_mlflow, \
         patch("training_pipeline.train.pd.read_parquet") as mock_read, \
         patch("training_pipeline.train.xgb.XGBClassifier") as mock_xgb, \
         patch("training_pipeline.train.os.path.exists", return_value=True):
        
        # Setup Mock Data
        df = pd.DataFrame({
            "diabetes": [0, 1] * 50,
            "gender": ["Male"] * 100,
            "smoking_history": ["never"] * 100,
            "feature1": [0.5] * 100
        })
        mock_read.return_value = df
        
        # Mock MLflow run context
        mock_active_run = MagicMock()
        mock_active_run.info.run_id = "test_run_id"
        mock_mlflow.start_run.return_value.__enter__.return_value = mock_active_run
        mock_mlflow.active_run.return_value = mock_active_run
        
        # FIX: Ensure predict returns a list, not a Mock, for accuracy_score
        mock_xgb.return_value.predict.side_effect = lambda x: [0] * len(x)
        
        # Run
        train_model()
        
        # Verify
        assert mock_mlflow.xgboost.autolog.called
        assert mock_mlflow.start_run.called
        assert mock_xgb.return_value.fit.called
        assert mock_mlflow.log_metric.called
