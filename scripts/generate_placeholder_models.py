
import pickle
import os
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Define model paths
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
MODELS = {
    "diabetes_model.pkl": {"type": "classifier", "classes": [0, 1], "features": 9},
    "heart_disease_model.pkl": {"type": "classifier", "classes": [0, 1], "features": 11}, # Fixed: Backend expects int 0/1, not strings
    "liver_disease_model.pkl": {"type": "classifier", "classes": [1, 2], "features": 10},
    "liver_scaler.pkl": {"type": "scaler", "features": 10},
    "kidney_model.pkl": {"type": "classifier", "classes": [0, 1], "features": 24}, # Fixed classes to 0/1 for consistency if needed, checking backend
    "kidney_scaler.pkl": {"type": "scaler", "features": 24},
    "lungs_model.pkl": {"type": "classifier", "classes": [0, 1], "features": 15}, # Backend expects 0/1 (Healthy/Respiratory Issue)
    "lungs_scaler.pkl": {"type": "scaler", "features": 15},
}

def generate_placeholders():
    print(f"Checking for models in: {BACKEND_DIR}")
    
    if not os.path.exists(BACKEND_DIR):
        os.makedirs(BACKEND_DIR)

    for filename, config in MODELS.items():
        filepath = os.path.join(BACKEND_DIR, filename)
        
        if os.path.exists(filepath):
            print(f"FOUND existing: {filename}")
            continue
            
        print(f"MISSING: {filename}. Generating placeholder...")
        
        obj = None
        if config["type"] == "classifier":
            # Create a simple dummy classifier
            n_features = config.get("features", 1)
            X = np.zeros((2, n_features)) # Create at least 2 samples to be safe
            y = np.array(config["classes"][:2]) if len(config["classes"]) >=2 else np.array([config["classes"][0]] * 2)
            # Ensure y matches X length
            if len(y) < 2: y = np.array([config["classes"][0]] * 2)
                
            clf = DummyClassifier(strategy="constant", constant=config["classes"][0])
            clf.fit(X, y)
            obj = clf
            
        elif config["type"] == "scaler":
            n_features = config.get("features", 1)
            scaler = StandardScaler()
            # Fit on zero array of correct shape
            scaler.fit(np.zeros((1, n_features)))
            obj = scaler

        with open(filepath, "wb") as f:
            pickle.dump(obj, f)
        print(f"CREATED placeholder: {filename}")

if __name__ == "__main__":
    generate_placeholders()
