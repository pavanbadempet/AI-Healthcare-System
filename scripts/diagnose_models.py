
import pickle
import os
import sys

BASE_DIR = os.path.join(os.getcwd(), "backend")
MODELS = ["diabetes_model.pkl", "heart_disease_model.pkl", "liver_scaler.pkl", "liver_disease_model.pkl", "kidney_model.pkl", "lungs_model.pkl"]

print(f"Checking models in {BASE_DIR}")
for m in MODELS:
    path = os.path.join(BASE_DIR, m)
    if not os.path.exists(path):
        print(f"MISSING: {path}")
        continue
        
    try:
        with open(path, "rb") as f:
            obj = pickle.load(f)
        print(f"SUCCESS: {m} loaded. Type: {type(obj)}")
    except Exception as e:
        print(f"FAIL: {m} failed to load. Error: {e}")
