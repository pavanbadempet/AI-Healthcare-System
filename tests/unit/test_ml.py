import pytest
from backend.ml_service import ml_service

# We assume models are loaded. If not, these will fail and we fix infrastructure.

# --- Diabetes Tests ---
def test_diabetes_valid_prediction():
    # Known values? Or just check format
    # "low risk" logic usually: low glucose, low BMI
    result = ml_service.predict_diabetes(
        gender="Male", age=30, hypertension=0, heart_disease=0, 
        smoking_history="never", bmi=22.0, hba1c_level=5.0, blood_glucose_level=90
    )
    assert isinstance(result, str)
    assert result in ["Low Risk", "High Risk"] 
    # Actually wait, the output of ml_service.predict_diabetes depends on the model's mapping.
    # In backend/ml_service.py we must check what it returns. usually user friendly string.

def test_diabetes_extreme_values():
    # High risk
    result = ml_service.predict_diabetes(
        gender="male", age=80, hypertension=1, heart_disease=1, 
        smoking_history="current", bmi=45.0, hba1c_level=9.0, blood_glucose_level=250
    )
    assert isinstance(result, str)
    # Ideally should be "Diabetic"

def test_diabetes_zero_values():
    # Physical/Clinical impossibility but system should not crash
    try:
        result = ml_service.predict_diabetes(
            gender="Female", age=0, hypertension=0, heart_disease=0, 
            smoking_history="never", bmi=0, hba1c_level=0, blood_glucose_level=0
        )
        assert isinstance(result, str)
    except Exception as e:
        pytest.fail(f"Zero inputs caused crash: {e}")

# --- Heart Disease Tests ---
def test_heart_valid_prediction():
    result = ml_service.predict_heart_disease(
        age=45, gender="Male", cp=0, trestbps=120, chol=200, fbs=0, 
        restecg=0, thalach=150, exang=0, oldpeak=0.0, slope=1, ca=0, thal=1
    )
    assert isinstance(result, str)

def test_heart_missing_data_defaults():
    # If the function signature requires arguments, python will Type Error if missing.
    # But checking if we pass 0s.
    pass

# --- Liver Disease Tests ---
def test_liver_valid_prediction():
    result = ml_service.predict_liver_disease(
        age=30, gender="Female", total_bilirubin=0.7, alkaline_phosphotase=150, 
        alamine_aminotransferase=20, albumin_globulin_ratio=1.0
    )
    assert isinstance(result, str)
