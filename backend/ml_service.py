import logging

from . import schemas
from .model_service import model_service

logger = logging.getLogger(__name__)
ML_PREDICTION_FAILURE_MESSAGE = "Error running prediction. Please try again later."

class MLService:
    def __init__(self):
        # We rely on backend.prediction's global state
        # Ensure they are initialized (idempotent)
        # prediction.initialize_models() # REMOVED: Managed by lifespan in main.py
        pass

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

            result = model_service.predict_diabetes(data)
            return result.prediction

        except Exception:
            logger.error("Legacy diabetes prediction failed")
            return ML_PREDICTION_FAILURE_MESSAGE

    def predict_heart_disease(self, age, gender, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal):
        try:
            g_val = 1 if str(gender).lower() == 'male' else 0

            data = schemas.HeartInput(
                age=float(age),
                sex=g_val,
                cp=int(cp),
                trestbps=float(trestbps),
                chol=float(chol),
                fbs=int(fbs),
                restecg=int(restecg),
                thalach=float(thalach),
                exang=int(exang),
                oldpeak=float(oldpeak),
                slope=int(slope),
                ca=int(ca),
                thal=int(thal)
            )

            result = model_service.predict_heart(data)
            return result.prediction
        except Exception:
             logger.error("Legacy heart prediction failed")
             return ML_PREDICTION_FAILURE_MESSAGE

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

            result = model_service.predict_liver(data)
            return result.prediction
        except Exception:
            logger.error("Legacy liver prediction failed")
            return ML_PREDICTION_FAILURE_MESSAGE

ml_service = MLService()

