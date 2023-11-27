import pickle
import numpy as np
import os

# Paths to models (in root directory)
# Paths to models (in root directory)
DIABETES_MODEL_PATH = "Diabetes Model.pkl"
HEART_MODEL_PATH = "Heart Disease Model.pkl"
LIVER_MODEL_PATH = "Liver Disease Model.pkl"
LIVER_SCALER_PATH = "LiverScaler.pkl"

class MLService:
    def __init__(self):
        self.diabetes_model = None
        self.heart_model = None
        self.liver_model = None
        self.liver_scaler = None
        self.load_models()

    def load_models(self):
        try:
            if os.path.exists(DIABETES_MODEL_PATH):
                self.diabetes_model = pickle.load(open(DIABETES_MODEL_PATH, 'rb'))
            if os.path.exists(HEART_MODEL_PATH):
                self.heart_model = pickle.load(open(HEART_MODEL_PATH, 'rb'))
            if os.path.exists(LIVER_MODEL_PATH):
                self.liver_model = pickle.load(open(LIVER_MODEL_PATH, 'rb'))
            if os.path.exists(LIVER_SCALER_PATH):
                self.liver_scaler = pickle.load(open(LIVER_SCALER_PATH, 'rb'))
            print("ML Models loaded successfully.")
        except Exception as e:
            print(f"Error loading ML models: {e}")

    def predict_diabetes(self, gender, age, hypertension, heart_disease, smoking_history, bmi, hba1c_level, blood_glucose_level):
        if not self.diabetes_model:
            return "Error: Diabetes Model not loaded."
        
        try:
            # Safe Casting
            age = float(age)
            hypertension = float(hypertension)
            heart_disease = float(heart_disease)
            bmi = float(bmi)
            hba1c_level = float(hba1c_level)
            blood_glucose_level = float(blood_glucose_level)
            
            # Mapping inputs to model format
            # Gender: Female=0, Male=1
            gender_val = 1.0 if str(gender).lower() == 'male' else 0.0
            
            # Smoking
            smoking_map = {'never': 0, 'unknown': 1, 'current': 2, 'former': 3, 'ever': 4, 'not current': 5}
            smoking_key = str(smoking_history).lower()
            if smoking_key not in smoking_map: smoking_key = 'unknown'
            smoking_val = float(smoking_map.get(smoking_key, 1))
            
            input_data = np.array([[gender_val, age, hypertension, heart_disease, smoking_val, bmi, hba1c_level, blood_glucose_level]], dtype=object)
            input_data = input_data.astype(float)
            
            prediction = self.diabetes_model.predict(input_data)
            return "High Risk" if prediction[0] == 1 else "Low Risk"
        except Exception as e:
            return f"Error running diabetes prediction: {e}"

    def predict_heart_disease(self, age, gender, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal):
        if not self.heart_model:
            return "Error: Heart Disease Model not loaded."
            
        try:
            # Safe Casting
            age = float(age)
            cp = float(cp)
            trestbps = float(trestbps)
            chol = float(chol)
            fbs = float(fbs)
            restecg = float(restecg)
            thalach = float(thalach)
            exang = float(exang)
            oldpeak = float(oldpeak)
            slope = float(slope)
            ca = float(ca)
            
            gender_val = 1.0 if str(gender).lower() == 'male' else 0.0
            
            # Thal Map: Normal=0, Fixed=1, Reversible=2
            thal_str = str(thal).lower()
            if "normal" in thal_str: thal_val = 0.0
            elif "fixed" in thal_str: thal_val = 1.0
            else: thal_val = 2.0
                
            input_data = np.array([[age, gender_val, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal_val]], dtype=object)
            input_data = input_data.astype(float)
            
            prediction = self.heart_model.predict(input_data)
            return "Heart Disease Detected" if prediction[0] == 1 else "Healthy Heart"
        except Exception as e:
             return f"Error running heart prediction: {e}"

    def predict_liver_disease(self, age, gender, total_bilirubin, alkaline_phosphotase, alamine_aminotransferase, albumin_globulin_ratio):
        if not self.liver_model or not self.liver_scaler:
            return "Error: Liver Model or Scaler not loaded."
            
        gender_val = 1.0 if str(gender).lower() == 'male' else 0.0
        
        try:
            import pandas as pd
            # Construct DataFrame with correct column names for Scaler
            input_dict = {
                'Age': [float(age)], 
                'Gender': [gender_val], 
                'Total_Bilirubin': [float(total_bilirubin)], 
                'Alkaline_Phosphotase': [float(alkaline_phosphotase)], 
                'Alamine_Aminotransferase': [float(alamine_aminotransferase)], 
                'Albumin_and_Globulin_Ratio': [float(albumin_globulin_ratio)]
            }
            df = pd.DataFrame(input_dict)
            
            # Log Transform Skewed Features (Matching training logic)
            skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase','Albumin_and_Globulin_Ratio']
            df[skewed] = np.log1p(df[skewed])
            
            # Scale Attributes (Matching training logic: all except Dataset were scaled)
            # The scaler anticipates all 6 columns because we fitted on `liver_data[attributes]` where attributes included Age, Gender, etc.
            # In train_liver.py: attributes = [col for col in df.columns if col != 'Dataset'] -> This includes Age, Gender, etc.
            cols_to_scale = ['Age', 'Gender', 'Total_Bilirubin', 'Alkaline_Phosphotase','Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
            df[cols_to_scale] = self.liver_scaler.transform(df[cols_to_scale])
            
            prediction = self.liver_model.predict(df)
            return "Liver Disease Detected" if prediction[0] == 1 else "Healthy Liver"
        except Exception as e:
            return f"Error running liver prediction: {e}"

ml_service = MLService()
