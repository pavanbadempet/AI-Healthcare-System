import pickle
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
import sys

# Define Router
router = APIRouter()

# --- Load Models (Global Scope - Load Once) ---
print("--- Loading ML Models into Memory ---")
try:
    with open("Diabetes Model.pkl", 'rb') as f:
        diabetes_model = pickle.load(f)
    print("✔ Diabetes Model Loaded")

    with open("Heart Disease Model.pkl", 'rb') as f:
        heart_model = pickle.load(f)
    print("✔ Heart Model Loaded")

    with open("Liver Disease Model.pkl", 'rb') as f:
        liver_model = pickle.load(f)
    print("✔ Liver Model Loaded")
    
    with open("Scaler.pkl", 'rb') as f:
        scaler = pickle.load(f)
    print("✔ Scaler Loaded")

except Exception as e:
    print(f"❌ Error Loading Models: {e}")
    diabetes_model = None
    heart_model = None
    liver_model = None
    scaler = None

# --- Input Schemas ---
class DiabetesInput(BaseModel):
    gender: float
    age: float
    hypertension: float
    heart_disease: float
    smoking: float
    bmi: float
    hba1c: float
    glucose: float

class HeartInput(BaseModel):
    age: float
    gender: float
    cp: float
    trestbps: float
    chol: float
    fbs: float
    restecg: float
    thalach: float
    exang: float
    oldpeak: float
    slope: float
    ca: float
    thal: float

class LiverInput(BaseModel):
    age: float
    gender: float
    total_bilirubin: float
    alkaline_phosphotase: float
    alamine_aminotransferase: float
    albumin_globulin_ratio: float

# --- Prediction Endpoints ---

@router.post("/predict/diabetes")
def predict_diabetes(data: DiabetesInput):
    if not diabetes_model:
        raise HTTPException(status_code=503, detail="Diabetes Model not available")
    try:
        input_data = np.array([[
            data.gender, data.age, data.hypertension, data.heart_disease, 
            data.smoking, data.bmi, data.hba1c, data.glucose
        ]], dtype=object).astype(float)
        
        prediction = diabetes_model.predict(input_data)
        result = "High Risk" if prediction[0] == 1 else "Low Risk"
        return {"prediction": result, "raw": int(prediction[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/heart")
def predict_heart(data: HeartInput):
    if not heart_model:
        raise HTTPException(status_code=503, detail="Heart Model not available")
    try:
        input_data = np.array([[
            data.age, data.gender, data.cp, data.trestbps, data.chol, data.fbs, 
            data.restecg, data.thalach, data.exang, data.oldpeak, data.slope, 
            data.ca, data.thal
        ]], dtype=object).astype(float)
        
        prediction = heart_model.predict(input_data)
        result = "Heart Disease Detected" if prediction[0] == 1 else "Healthy Heart"
        return {"prediction": result, "raw": int(prediction[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/liver")
def predict_liver(data: LiverInput):
    if not liver_model or not scaler:
        raise HTTPException(status_code=503, detail="Liver Model or Scaler not available")
    try:
        # Preprocessing similar to frontend logic
        # ["Age", "Gender", "Total_Bilirubin", "Alkaline_Phosphotase", "Alamine_Aminotransferase", "Albumin_and_Globulin_Ratio"]
        input_list = [
            data.age, data.gender, data.total_bilirubin, 
            data.alkaline_phosphotase, data.alamine_aminotransferase, 
            data.albumin_globulin_ratio
        ]
        cols = ['Age', 'Gender', 'Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
        df = pd.DataFrame([input_list], columns=cols)
        
        # Log Transform Skewed
        skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
        df[skewed] = np.log1p(df[skewed])
        
        # Scale
        df[cols] = scaler.transform(df[cols])
        
        prediction = liver_model.predict(df)
        # Original logic: 0 = Healthy, 1 = Disease (Check mapping carefully, assuming 1=Disease based on common datasets, but frontend said 0=Healthy)
        # Frontend logic: prediction[0] == 0 => Healthy.
        
        result = "Healthy Liver" if prediction[0] == 0 else "Liver Disease Detected"
        return {"prediction": result, "raw": int(prediction[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
