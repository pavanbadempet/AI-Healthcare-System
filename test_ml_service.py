import sys
import os
# Add root to sys path to allow backend imports
sys.path.append(os.getcwd())

from backend.ml_service import ml_service

def test_predictions():
    print("Testing Diabetes Prediction...")
    # High risk mock data
    res = ml_service.predict_diabetes(
        gender="Male", age=60, hypertension=1, heart_disease=1, 
        smoking_history="current", bmi=35.0, hba1c_level=9.0, blood_glucose_level=200
    )
    print(f"Diabetes Result: {res}")

    print("\nTesting Heart Prediction...")
    # Mock data
    res = ml_service.predict_heart_disease(
        age=60, gender="Male", cp=0, trestbps=140, chol=250, fbs=1, 
        restecg=0, thalach=150, exang=1, oldpeak=2.0, slope=1, ca=0, thal="Fixed Defect"
    )
    print(f"Heart Result: {res}")

if __name__ == "__main__":
    test_predictions()
