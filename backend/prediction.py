import pickle
import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
import os
import logging
from typing import Dict, Any, List
from functools import lru_cache

# --- Custom Modules ---
from . import explainability, schemas

# --- Logging Configuration ---
logger = logging.getLogger(__name__)

# --- Router Definition ---
router = APIRouter()

# --- Global Model State ---
diabetes_model = None
heart_model = None
liver_model = None
liver_scaler = None
kidney_model = None
kidney_scaler = None
lungs_model = None
lungs_scaler = None

# --- Path Configuration ---
# Robustly find the models directory regardless of CWD.
# Models are located in the SAME directory as this file (backend/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = BASE_DIR

class DummyModel:
    """Simple placeholder used when a real model cannot be loaded."""
    def predict(self, X):
        # Checks if tests expect errors or just want an object
        raise RuntimeError("Model not available (DummyModel)")

class DummyScaler:
    """Simple placeholder for scalers used when loading fails."""
    def transform(self, X):
        raise RuntimeError("Scaler not available (DummyScaler)")

def load_pkl(filenames: List[str], fallback_class=None):
    """
    Attempt to load a pickle file from a list of potential names in the models directory.
    Returns the loaded object or an instance of fallback_class if provided.
    """
    for f_name in filenames:
        path = os.path.join(MODEL_DIR, f_name)
        if os.path.exists(path):
            try:
                # Use joblib to load (supports standard pickle and compressed joblib files)
                with open(path, 'rb') as f:
                    obj = joblib.load(f)
                    logger.info(f"✅ Successfully loaded model: {f_name}")
                    return obj
            except Exception as e:
                logger.error(f"❌ Failed to load {f_name}: {e}")
    
    logger.warning(f"⚠️ Could not find any of: {filenames} in {MODEL_DIR}. Model will be unavailable.")
    if fallback_class:
        return fallback_class()
    return None

@lru_cache(maxsize=10)
def load_pkl_cached(filename_tuple):
    return load_pkl(list(filename_tuple))

def initialize_models():
    """Load all models into global state, using dummy fallbacks when files are missing."""
    global diabetes_model, heart_model, liver_model, liver_scaler, kidney_model, kidney_scaler, lungs_model, lungs_scaler
    logger.info("Loading models...")
    diabetes_model = load_pkl(["diabetes_model.pkl"], fallback_class=DummyModel)
    heart_model = load_pkl(["heart_disease_model.pkl"], fallback_class=DummyModel)
    liver_model = load_pkl(["liver_disease_model.pkl"], fallback_class=DummyModel)
    liver_scaler = load_pkl(["liver_scaler.pkl"], fallback_class=DummyScaler)
    
    # Load Kidney and Lungs models (dummy if missing)
    kidney_model = load_pkl(["kidney_model.pkl"], fallback_class=DummyModel)
    kidney_scaler = load_pkl(["kidney_scaler.pkl"], fallback_class=DummyScaler)
    lungs_model = load_pkl(["lungs_model.pkl"], fallback_class=DummyModel)
    lungs_scaler = load_pkl(["lungs_scaler.pkl"], fallback_class=DummyScaler)

# Initialize on import is REMOVED to prevent startup blocking
# initialize_models() must be called explicitly by the app startup or tests
pass

from . import auth, models as db_models
from fastapi import Depends

@router.post("/admin/reload_models")
def reload_models(current_user: db_models.User = Depends(auth.get_current_user)):
    """Force reload of all models from disk (Zero-Downtime Update). Admin only."""
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    initialize_models()
    return {
        "status": "Models Reloaded", 
        "diabetes_loaded": diabetes_model is not None,
        "heart_loaded": heart_model is not None,
        "liver_loaded": liver_model is not None,
        "kidney_loaded": kidney_model is not None,
        "lungs_loaded": lungs_model is not None
    }

# --- Helper Functions for Big Data Mapping ---

def get_age_bucket(age: float) -> int:
    """Map Age (Years) to BRFSS Age Bucket (1-13)."""
    if age <= 24: return 1
    elif age <= 29: return 2
    elif age <= 34: return 3
    elif age <= 39: return 4
    elif age <= 44: return 5
    elif age <= 49: return 6
    elif age <= 54: return 7
    elif age <= 59: return 8
    elif age <= 64: return 9
    elif age <= 69: return 10
    elif age <= 74: return 11
    elif age <= 79: return 12
    else: return 13

# --- Prediction Endpoints ---

@router.post("/predict/kidney", response_model=Dict[str, Any])
def predict_kidney(data: schemas.KidneyInput) -> Dict[str, Any]:
    if not kidney_model or not kidney_scaler:
         raise HTTPException(status_code=503, detail="Kidney Model not trained/loaded.")
             
    try:
        # Features Verified: ['age', 'bp', 'sg', 'al', 'su', 'rbc', 'pc', 'pcc', 'ba', 'bgr', 'bu', 'sc', 'sod', 'pot', 'hemo', 'pcv', 'wc', 'rc', 'htn', 'dm', 'cad', 'appet', 'pe', 'ane']
        feature_names = ['age', 'bp', 'sg', 'al', 'su', 'rbc', 'pc', 'pcc', 'ba', 'bgr', 'bu', 'sc', 'sod', 'pot', 'hemo', 'pcv', 'wc', 'rc', 'htn', 'dm', 'cad', 'appet', 'pe', 'ane']
        
        input_list = [
            data.age, data.bp, data.sg, data.al, data.su, 
            data.rbc, data.pc, data.pcc, data.ba, 
            data.bgr, data.bu, data.sc, data.sod, data.pot, data.hemo, data.pcv, data.wc, data.rc,
            data.htn, data.dm, data.cad, data.appet, data.pe, data.ane
        ]
        
        # DataFrame to fix StandardScaler feature checks
        df = pd.DataFrame([input_list], columns=feature_names)
        input_scaled = kidney_scaler.transform(df)
        
        prediction = kidney_model.predict(input_scaled)[0]
        # Handle string or int
        raw_pred = 1 if (str(prediction) == '1' or prediction == 1 or str(prediction).lower() == 'chronic kidney disease detected') else 0
        result = "Chronic Kidney Disease Detected" if raw_pred == 1 else "Healthy Kidney"
        return {"prediction": result, "raw": raw_pred}
        
    except Exception as e:
        logger.error(f"Kidney Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/lungs", response_model=Dict[str, Any])
def predict_lungs(data: schemas.LungInput) -> Dict[str, Any]:
    if not lungs_model or not lungs_scaler:
         raise HTTPException(status_code=503, detail="Lung Model not trained/loaded.")
             
    try:
        # Features Verified: UPPERCASE ['GENDER', 'AGE', 'SMOKING', ...]
        feature_names = ['GENDER', 'AGE', 'SMOKING', 'YELLOW_FINGERS', 'ANXIETY', 'PEER_PRESSURE', 'CHRONIC_DISEASE', 'FATIGUE', 'ALLERGY', 'WHEEZING', 'ALCOHOL_CONSUMING', 'COUGHING', 'SHORTNESS_OF_BREATH', 'SWALLOWING_DIFFICULTY', 'CHEST_PAIN']
        
        input_list = [
            data.gender, data.age, data.smoking, data.yellow_fingers,
            data.anxiety, data.peer_pressure, data.chronic_disease, data.fatigue,
            data.allergy, data.wheezing, data.alcohol, data.coughing,
            data.shortness_of_breath, data.swallowing_difficulty, data.chest_pain
        ]
        
        # DataFrame to fix StandardScaler feature checks
        df = pd.DataFrame([input_list], columns=feature_names)
        input_scaled = lungs_scaler.transform(df)
        
        prediction = lungs_model.predict(input_scaled)[0]
        # Robust handling
        raw_pred = 1 if (str(prediction) == '1' or prediction == 1 or str(prediction).upper() == 'HIGH' or str(prediction).upper() == 'MEDIUM') else 0
        result = "Respiratory Issue Detected" if raw_pred == 1 else "Healthy Lungs"
        return {"prediction": result, "raw": raw_pred}
        
    except Exception as e:
        logger.error(f"Lung Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/diabetes", response_model=Dict[str, Any])
def predict_diabetes(data: schemas.DiabetesInput) -> Dict[str, Any]:
    if not diabetes_model:
        raise HTTPException(status_code=503, detail="Diabetes Model not available")
    try:
        age_bucket = get_age_bucket(data.age)
        input_list = [
            data.hypertension, data.high_chol, data.bmi, data.smoking_history,
            data.heart_disease, data.physical_activity, data.general_health,
            data.gender, age_bucket
        ]
        # DummyModel returns [0]; ensure we handle both list and scalar
        prediction = diabetes_model.predict([input_list])
        if isinstance(prediction, (list, tuple, np.ndarray)):
            prediction = prediction[0]
        # Handle numpy scalar
        if hasattr(prediction, 'item'):
            prediction = prediction.item()
        result = "High Risk" if prediction == 1 or prediction == 2 else "Low Risk"
        return {"prediction": result, "raw": int(prediction)}
    except Exception as e:
        logger.error(f"Diabetes Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/heart", response_model=Dict[str, Any])
def predict_heart(data: schemas.HeartInput) -> Dict[str, Any]:
    if not heart_model:
        raise HTTPException(status_code=503, detail="Heart Model not available")
    try:
        age_bucket = get_age_bucket(data.age)
        input_list = [
            data.high_bp, data.high_chol, data.bmi, data.smoker,
            data.stroke, data.diabetes, data.phys_activity,
            data.hvy_alcohol, data.gen_hlth, data.gender, age_bucket
        ]
        prediction = heart_model.predict([input_list])
        if isinstance(prediction, (list, tuple, np.ndarray)):
            prediction = prediction[0]
        # Handle numpy scalar
        if hasattr(prediction, 'item'):
            prediction = prediction.item()
        result = "Heart Disease Detected" if (prediction == 1 or str(prediction) == '1' or str(prediction) == 'Heart Disease Detected') else "Healthy Heart"
        # Return 0 or 1 for raw
        raw_val = 1 if result == "Heart Disease Detected" else 0
        return {"prediction": result, "raw": raw_val}
    except Exception as e:
        logger.error(f"Heart Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/liver", response_model=Dict[str, Any])
def predict_liver(data: schemas.LiverInput) -> Dict[str, Any]:
    if not liver_model or not liver_scaler:
        raise HTTPException(status_code=503, detail="Liver Model or Scaler not available")
    try:
        # Features Verified: Title Case ['Age', 'Gender', 'Total_Bilirubin', ...]
        feature_names = ['Age', 'Gender', 'Total_Bilirubin', 'Direct_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Aspartate_Aminotransferase', 'Total_Proteins', 'Albumin', 'Albumin_and_Globulin_Ratio']
        
        # Data List
        input_list = [
            data.age, data.gender, data.total_bilirubin, data.direct_bilirubin,
            data.alkaline_phosphotase, data.alamine_aminotransferase, 
            data.aspartate_aminotransferase, data.total_proteins, 
            data.albumin, data.albumin_and_globulin_ratio
        ]
        
        # Create DataFrame
        df = pd.DataFrame([input_list], columns=feature_names)
        
        # Apply Log Transform to skewed features (Use Title Case names)
        skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
        for col in skewed:
            df[col] = np.log1p(df[col])
            
        # Scale with dedicated Liver Scaler
        X_scaled = liver_scaler.transform(df)
        
        # Predict
        prediction = liver_model.predict(X_scaled)
        val = prediction[0]
        result = "Liver Disease Detected" if val == 1 else "Healthy Liver"
        return {"prediction": result, "raw": int(val)}

    except Exception as e:
        import traceback
        error_msg = f"Liver Logic Error: {str(e)} | Trace: {traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=f"Liver Prediction Failed: {str(e)}")

# --- Explanation Endpoints (SHAP) ---

@router.post("/predict/explain/diabetes")
def explain_diabetes(data: schemas.DiabetesInput):
    if not diabetes_model:
        raise HTTPException(status_code=503, detail="Model unavailable")
    
    age_bucket = get_age_bucket(data.age)
    input_list = [
        data.hypertension, data.high_chol, data.bmi, data.smoking_history, 
        data.heart_disease, data.physical_activity, data.general_health, 
        data.gender, age_bucket
    ]
    feature_names = ['Hypertension', 'HighChol', 'BMI', 'Smoking', 'HeartDisease', 'PhysActivity', 'GenHlth', 'Gender', 'AgeBucket']
    
    explanation = explainability.get_shap_values(diabetes_model, np.array([input_list]), feature_names)
    if explanation: return explanation
    raise HTTPException(status_code=500, detail="Explanation Generation Failed")

@router.post("/predict/explain/heart")
def explain_heart(data: schemas.HeartInput):
    if not heart_model:
        raise HTTPException(status_code=503, detail="Model unavailable")
    
    age_bucket = get_age_bucket(data.age)
    input_list = [
        data.high_bp, data.high_chol, data.bmi, data.smoker, 
        data.stroke, data.diabetes, data.phys_activity, 
        data.hvy_alcohol, data.gen_hlth, data.gender, age_bucket
    ]
    feature_names = ['HighBP', 'HighChol', 'BMI', 'Smoker', 'Stroke', 'Diabetes', 'PhysActivity', 'HvyAlcohol', 'GenHlth', 'Gender', 'AgeBucket']
    
    explanation = explainability.get_shap_values(heart_model, np.array([input_list]), feature_names)
    if explanation: return explanation
    raise HTTPException(status_code=500, detail="Explanation Generation Failed")

@router.post("/predict/explain/liver")
def explain_liver(data: schemas.LiverInput):
    if not liver_model or not liver_scaler:
         raise HTTPException(status_code=503, detail="Model unavailable")
    
    feature_names = ['Age', 'Gender', 'Total_Bilirubin', 'Direct_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Aspartate_Aminotransferase', 'Total_Proteins', 'Albumin', 'Albumin_and_Globulin_Ratio']
    input_list = [
        data.age, data.gender, data.total_bilirubin, data.direct_bilirubin,
        data.alkaline_phosphotase, data.alamine_aminotransferase, 
        data.aspartate_aminotransferase, data.total_proteins, 
        data.albumin, data.albumin_and_globulin_ratio
    ]
    df = pd.DataFrame([input_list], columns=feature_names)
    skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
    for col in skewed:
        df[col] = np.log1p(df[col])
    
    X_scaled = liver_scaler.transform(df)
    
    explanation = explainability.get_shap_values(liver_model, X_scaled, feature_names)
    if explanation: return explanation
    raise HTTPException(status_code=500, detail="Explanation Generation Failed")
