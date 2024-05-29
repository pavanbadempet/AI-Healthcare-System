import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
import os
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# --- Configuration ---
# Robust path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "diabetes.parquet")
MODEL_PATH = os.path.join(BASE_DIR, "Diabetes Model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "Scaler.pkl")

def train_diabetes_model():
    print("Starting Diabetes Model Training...")

    # 1. Load Data
    # 1. Load Data
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    df = pd.read_parquet(DATASET_PATH)
    print(f"Loaded Dataset: {len(df)} records")

    # 2. Preprocessing (Matching Notebook Logic)
    # Gender: Other->0, Male->1, Female->2
    # Note: Notebook removed '0' (Other). We will do the same.
    gender_map = {'Other': 0, 'Male': 1, 'Female': 2}
    df['gender'] = df['gender'].map(gender_map).fillna(df['gender'])
    df = df[df['gender'] != 0].copy()  # .copy() to avoid SettingWithCopyWarning
    
    # Smoking: never->0, No Info->1, current->2, former->3, ever->4, not current->5
    smoking_map = {'never': 0, 'No Info': 1, 'current': 2, 'former': 3, 'ever': 4, 'not current': 5}
    df['smoking_history'] = df['smoking_history'].map(smoking_map).fillna(df['smoking_history'])

    print("Preprocessing Complete")

    # 3. Features & Target
    X = df.drop("diabetes", axis=1)
    Y = df["diabetes"]

    # 4. Train/Test Split
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

    # 5. Training (XGBoost)
    # Note: No scaling is performed, matching the notebook and ml_service behavior.
    model = xgb.XGBClassifier(eval_metric='logloss')
    model.fit(X_train, Y_train)

    # 6. Evaluation
    y_pred = model.predict(X_test)
    acc = accuracy_score(Y_test, y_pred)
    print(f"Model Trained. Accuracy: {acc:.4f}")

    # 7. Save Model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model Saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_diabetes_model()
