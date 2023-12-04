import pickle
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import os
import logging
from typing import Dict, Any, List
from functools import lru_cache

# --- Custom Modules ---
from . import explainability  # Custom Module for SHAP

# --- Logging Configuration ---
# logging.basicConfig(level=logging.INFO) # Handled in main.py
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
# Robustly find the models directory regardless of CWD
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'models')

def load_pkl(filenames: List[str]):
    """
    Attempt to load a pickle file from a list of potential names in the models directory.
    Returns the loaded object or None if not found.
    """
    for f_name in filenames:
        path = os.path.join(MODEL_DIR, f_name)
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    obj = pickle.load(f)
                    logger.info(f"✅ Successfully loaded model: {f_name}")
                    return obj
            except Exception as e:
                logger.error(f"❌ Failed to load {f_name}: {e}")
    
    logger.warning(f"⚠️ Could not find any of: {filenames} in {MODEL_DIR}")
    return None

@lru_cache(maxsize=10)
def load_pkl_cached(filename_tuple):
    return load_pkl(list(filename_tuple))

def initialize_models():
    """Load all models into global state."""
    global diabetes_model, heart_model, liver_model, liver_scaler, kidney_model, kidney_scaler, lungs_model, lungs_scaler
    logger.info("Loading models...")
    diabetes_model = load_pkl(["diabetes_model.pkl", "Diabetes Model.pkl"])
    heart_model = load_pkl(["heart_disease_model.pkl", "Heart Disease Model.pkl"])
    liver_model = load_pkl(["liver_disease_model.pkl", "Liver Disease Model.pkl"])
    liver_scaler = load_pkl(["LiverScaler.pkl", "liver_scaler.pkl"])
    
    # New: Eagerly load Kidney and Lungs to satisfy user expectation
    kidney_model = load_pkl(["kidney_model.pkl"])
    kidney_scaler = load_pkl(["kidney_scaler.pkl"])
    lungs_model = load_pkl(["lungs_model.pkl"])
    lungs_scaler = load_pkl(["lungs_scaler.pkl"])

# Initialize on import
initialize_models()

@router.post("/admin/reload_models")
def reload_models():
    """Force reload of all models from disk (Zero-Downtime Update)."""
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

# --- Data Schemas (Big Data Standard) ---

class DiabetesInput(BaseModel):
    """Schema for Diabetes Prediction (BRFSS 2015 Big Data)"""
    gender: int = Field(..., description="0: Female, 1: Male")
    age: float = Field(..., description="Age in years")
    hypertension: int = Field(..., description="0: No, 1: Yes")
    heart_disease: int = Field(..., description="0: No, 1: Yes")
    smoking_history: int = Field(..., description="0: No, 1: Yes")
    bmi: float = Field(..., description="Body Mass Index")
    high_chol: int = Field(..., description="0: No, 1: Yes")
    physical_activity: int = Field(..., description="0: No, 1: Yes (Past 30 days)")
    general_health: int = Field(..., description="1 (Excellent) to 5 (Poor)")

class HeartInput(BaseModel):
    """
    Schema for Heart Disease Prediction (CDC BRFSS - 90%+ Accuracy).
    Feature Logic: Focuses on Risk Factors (History) rather than just current Vitals.
    """
    age: float = Field(..., description="Age in years.")
    gender: int = Field(..., description="0: Female, 1: Male")
    high_bp: int = Field(..., description="0: Normal, 1: High BP")
    high_chol: int = Field(..., description="0: Normal, 1: High Cholesterol")
    bmi: float = Field(..., description="Body Mass Index")
    smoker: int = Field(..., description="1 if smoked 100+ cigs in lifetime, else 0")
    stroke: int = Field(..., description="1 if history of stroke, else 0")
    diabetes: int = Field(..., description="0: No, 1: Pre-Diabetes or Diabetes")
    phys_activity: int = Field(..., description="1 if active in past 30 days, else 0")
    hvy_alcohol: int = Field(..., description="1 if heavy drinker (Men >14/wk, Women >7/wk), else 0")
    gen_hlth: int = Field(..., description="Self-rated health: 1 (Excellent) to 5 (Poor)")

class LiverInput(BaseModel):
    """Schema for Liver Disease Prediction (ILPD)."""
    age: float
    gender: int # 0: Female, 1: Male
    total_bilirubin: float
    direct_bilirubin: float
    alkaline_phosphotase: float
    alamine_aminotransferase: float
    aspartate_aminotransferase: float
    total_proteins: float
    albumin: float
    albumin_and_globulin_ratio: float

class KidneyInput(BaseModel):
    """Schema for Kidney Disease Prediction (24 Features)."""
    age: float
    bp: float
    sg: float
    al: float
    su: float
    rbc: int # 0:Normal, 1:Abnormal
    pc: int
    pcc: int
    ba: int
    bgr: float
    bu: float
    sc: float
    sod: float
    pot: float
    hemo: float
    pcv: float
    wc: float
    rc: float
    htn: int # 1:Yes, 0:No
    dm: int
    cad: int
    appet: int # 0:Good, 1:Poor
    pe: int
    ane: int

class LungInput(BaseModel):
    """Schema for Respiratory/Lung Health."""
    gender: int # 1:Male, 0:Female
    age: float
    smoking: int
    yellow_fingers: int
    anxiety: int
    peer_pressure: int
    chronic_disease: int
    fatigue: int
    allergy: int
    wheezing: int
    alcohol: int
    coughing: int
    shortness_of_breath: int
    swallowing_difficulty: int
    chest_pain: int

# --- Prediction Endpoints ---

@router.post("/predict/kidney", response_model=Dict[str, Any])
def predict_kidney(data: KidneyInput) -> Dict[str, Any]:
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
        result = "Chronic Kidney Disease Detected" if prediction == 1 else "Healthy Kidney"
        return {"prediction": result, "raw": int(prediction)}
        
    except Exception as e:
        logger.error(f"Kidney Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/lungs", response_model=Dict[str, Any])
def predict_lungs(data: LungInput) -> Dict[str, Any]:
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
        result = "Respiratory Issue Detected" if prediction == 1 else "Healthy Lungs"
        return {"prediction": result, "raw": int(prediction)}
        
    except Exception as e:
        logger.error(f"Lung Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/diabetes", response_model=Dict[str, Any])
def predict_diabetes(data: DiabetesInput) -> Dict[str, Any]:
    if not diabetes_model:
        raise HTTPException(status_code=503, detail="Diabetes Model not available")
    try:
        age_bucket = get_age_bucket(data.age)
        input_list = [
            data.hypertension, data.high_chol, data.bmi, data.smoking_history, 
            data.heart_disease, data.physical_activity, data.general_health, 
            data.gender, age_bucket
        ]
        prediction = diabetes_model.predict([input_list])[0]
        result = "High Risk" if prediction == 1 or prediction == 2 else "Low Risk"
        return {"prediction": result, "raw": int(prediction)}
    except Exception as e:
        logger.error(f"Diabetes Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/heart", response_model=Dict[str, Any])
def predict_heart(data: HeartInput) -> Dict[str, Any]:
    if not heart_model:
        raise HTTPException(status_code=503, detail="Heart Model not available")
    try:
        age_bucket = get_age_bucket(data.age)
        input_list = [
            data.high_bp, data.high_chol, data.bmi, data.smoker, 
            data.stroke, data.diabetes, data.phys_activity, 
            data.hvy_alcohol, data.gen_hlth, data.gender, age_bucket
        ]
        
        prediction = heart_model.predict([input_list])[0]
        result = "Heart Disease Detected" if prediction == 1 else "Healthy Heart"
        return {"prediction": result, "raw": int(prediction)}
    except Exception as e:
        logger.error(f"Heart Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/liver", response_model=Dict[str, Any])
def predict_liver(data: LiverInput) -> Dict[str, Any]:
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
        print(error_msg) # Force print to stdout
        raise HTTPException(status_code=500, detail=f"Liver Prediction Failed: {str(e)}")

# --- Explanation Endpoints (SHAP) ---

@router.post("/predict/explain/diabetes")
def explain_diabetes(data: DiabetesInput):
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
def explain_heart(data: HeartInput):
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
def explain_liver(data: LiverInput):
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
