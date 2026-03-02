import os
import sys
import pandas as pd
import numpy as np
import traceback
from typing import Dict, Any

# Add the current directory to sys.path to allow imports from .
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from . import prediction
from . import schemas

def test_all_predictions():
    print("Testing all trained models with sample data...")
    
    # 1. Initialize models
    prediction.initialize_models()
    
    # 2. Test Diabetes
    try:
        diabetes_data = schemas.DiabetesInput(
            gender=1, age=50.0, hypertension=1, high_chol=1, 
            bmi=28.0, smoking_history=1, heart_disease=0, 
            physical_activity=1, general_health=3
        )
        res = prediction.predict_diabetes(diabetes_data)
        print(f"OK - Diabetes Prediction: {res}")
    except Exception as e:
        print(f"FAIL - Diabetes Prediction Error: {e}")
        traceback.print_exc()

    # 3. Test Heart
    try:
        heart_data = schemas.HeartInput(
            age=63, sex=1, cp=3, trestbps=145, chol=233, 
            fbs=1, restecg=0, thalach=150, exang=0, 
            oldpeak=2.3, slope=0, ca=0, thal=1
        )
        res = prediction.predict_heart(heart_data)
        print(f"OK - Heart Prediction: {res}")
    except Exception as e:
        print(f"FAIL - Heart Prediction Error: {e}")
        traceback.print_exc()

    # 4. Test Liver
    try:
        liver_data = schemas.LiverInput(
            age=65, gender=1, total_bilirubin=0.7, direct_bilirubin=0.1,
            alkaline_phosphotase=187, alamine_aminotransferase=16,
            aspartate_aminotransferase=18, total_proteins=6.8,
            albumin=3.3, albumin_and_globulin_ratio=0.9
        )
        res = prediction.predict_liver(liver_data)
        print(f"OK - Liver Prediction: {res}")
    except Exception as e:
        print(f"FAIL - Liver Prediction Error: {e}")
        traceback.print_exc()

    # 5. Test Kidney
    try:
        kidney_data = schemas.KidneyInput(
            age=48, bp=80, sg=1.02, al=1, su=0, rbc=0, pc=0, pcc=0, ba=0,
            bgr=121, bu=36, sc=1.2, sod=142, pot=4.9, hemo=15.4, pcv=44,
            wc=7800, rc=5.2, htn=1, dm=1, cad=0, appet=0, pe=0, ane=0
        )
        res = prediction.predict_kidney(kidney_data)
        print(f"OK - Kidney Prediction: {res}")
    except Exception as e:
        print(f"FAIL - Kidney Prediction Error: {e}")
        traceback.print_exc()

    # 6. Test Lungs
    try:
        lung_data = schemas.LungInput(
            gender=1, age=69, smoking=1, yellow_fingers=1, anxiety=1,
            peer_pressure=1, chronic_disease=1, fatigue=1, allergy=1,
            wheezing=1, alcohol=1, coughing=1, shortness_of_breath=1,
            swallowing_difficulty=1, chest_pain=1
        )
        res = prediction.predict_lungs(lung_data)
        print(f"OK - Lung Prediction: {res}")
    except Exception as e:
        print(f"FAIL - Lung Prediction Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_all_predictions()
