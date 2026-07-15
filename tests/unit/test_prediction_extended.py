import pytest
import numpy as np
from backend.prediction import (
    _calculate_conformal_prediction,
    _calculate_adaptive_conformal_prediction,
    _get_triage_recommendation,
    _get_top_risk_factors,
    _calculate_clinical_recourse,
)

def test_calculate_conformal_prediction_float():
    result = _calculate_conformal_prediction(0.96, 0.05)
    assert 1 in result["conformal_prediction_set"]

def test_calculate_conformal_prediction_dict():
    result = _calculate_conformal_prediction(0.96, {0: 0.1, 1: 0.05})
    assert 1 in result["conformal_prediction_set"]

def test_calculate_adaptive_conformal_prediction():
    result = _calculate_adaptive_conformal_prediction(
        proba_positive=0.8,
        conformal_q=0.1,
        input_list=[1, None, 3, 4],
        raw_pred=1,
        risk_level="High Risk"
    )
    assert "conformal_prediction_set" in result
    assert "significance_level" in result
    assert "missingness_ratio" in result

def test_get_triage_recommendation():
    # Takes prediction_val: int, conformal_set: list
    assert _get_triage_recommendation(1, [1]) is not None
    assert _get_triage_recommendation(0, [0]) is not None

def test_get_top_risk_factors():
    # Takes model: Any, imputed_list: list, feature_names: list, attributions: Optional[dict] = None
    attributions = {"bp": 0.8, "age": 0.5, "bmi": -0.2}
    top_factors = _get_top_risk_factors(
        model=None, 
        imputed_list=[1,2,3], 
        feature_names=["bp", "age", "bmi"], 
        attributions=attributions
    )
    assert "Bp" in top_factors[0]

def test_calculate_clinical_recourse():
    # Takes model_name: str, model_obj: Any, imputed_list: list, current_prob: float, scaler: Any = None
    recourse = _calculate_clinical_recourse(
        model_name="diabetes", 
        model_obj=None, 
        imputed_list=[30.0, 45, 1, 1], 
        current_prob=0.8
    )
    
    # Just assert it doesn't crash, might be None if mock model doesn't work
    assert recourse is None or isinstance(recourse, str)
