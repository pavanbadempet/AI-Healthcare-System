import numpy as np
import logging
from . import prediction, schemas

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        # We rely on backend.prediction's global state
        # Ensure they are initialized (idempotent)
        prediction.initialize_models()

    def predict_diabetes(self, gender, age, hypertension, heart_disease, smoking_history, bmi, hba1c_level, blood_glucose_level):
        try:
            # Map Inputs to Schema expected by prediction.py
            
            # Map Gender
            g_val = 1 if str(gender).lower() == 'male' else 0
            
            # Map smoking string to int (0-5)
            s_map = {'never': 0, 'current': 1, 'former': 2, 'ever': 3, 'not current': 4}
            s_val = s_map.get(str(smoking_history).lower(), 0)
            
            data = schemas.DiabetesInput(
                gender=g_val,
                age=float(age),
                hypertension=int(hypertension),
                heart_disease=int(heart_disease),
                smoking_history=s_val,
                bmi=float(bmi),
                high_chol=0, # Default
                physical_activity=0, # Default
                general_health=3 # Default 'Good'
            )
            
            result = prediction.predict_diabetes(data)
            return result["prediction"]
            
        except Exception as e:
            logger.error(f"Legacy Diabetes Predict Error: {e}")
            return f"Error running diabetes prediction: {e}"

    def predict_heart_disease(self, age, gender, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal):
        try:
            g_val = 1 if str(gender).lower() == 'male' else 0
            
            # Map legacy 'cp', 'trestbps' etc to HeartInput
            # HeartInput: high_bp, high_chol, bmi, smoker, stroke, diabetes, phys_activity, hvy_alcohol, gen_hlth, gender, age
            
            data = schemas.HeartInput(
                age=float(age),
                gender=g_val,
                high_bp=1 if float(trestbps) > 130 else 0,
                high_chol=1 if float(chol) > 200 else 0,
                bmi=25.0, # Default
                smoker=0,
                stroke=0,
                diabetes=1 if float(fbs) > 0 else 0,
                phys_activity=0,
                hvy_alcohol=0,
                gen_hlth=3
            )
             
            result = prediction.predict_heart(data)
            return result["prediction"]
        except Exception as e:
             logger.error(f"Legacy Heart Predict Error: {e}")
             return f"Error running heart prediction: {e}"

    def predict_liver_disease(self, age, gender, total_bilirubin, alkaline_phosphotase, alamine_aminotransferase, albumin_globulin_ratio):
        try:
            g_val = 1 if str(gender).lower() == 'male' else 0
            
            data = schemas.LiverInput(
                age=float(age),
                gender=g_val,
                total_bilirubin=float(total_bilirubin),
                alkaline_phosphotase=float(alkaline_phosphotase),
                alamine_aminotransferase=float(alamine_aminotransferase),
                albumin_and_globulin_ratio=float(albumin_globulin_ratio),
                # Defaults for new fields
                direct_bilirubin=0.5,
                aspartate_aminotransferase=30.0,
                total_proteins=6.0,
                albumin=3.0
            )
            
            result = prediction.predict_liver(data)
            return result["prediction"]
        except Exception as e:
            logger.error(f"Legacy Liver Predict Error: {e}")
            return f"Error running liver prediction: {e}"

ml_service = MLService()

