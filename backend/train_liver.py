import os
import pickle

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.utils import resample

try:
    from .features import LIVER_FEATURES
except ImportError:
    pass

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "liver.parquet")
MODEL_PATH = os.path.join(BASE_DIR, "liver_disease_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "liver_scaler.pkl")

def train_liver_model():
    print("Starting Liver Disease Model Training (Honest Evaluation)...")

    # 1. Load Data
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    df = pd.read_parquet(DATASET_PATH)
    print(f"Loaded Dataset: {len(df)} records")

    # 2. Preprocessing
    # Rename Columns to Title Case for API Compatibility
    column_mapping = {
        'age': 'Age', 'gender': 'Gender', 'total_bilirubin': 'Total_Bilirubin',
        'direct_bilirubin': 'Direct_Bilirubin', 'alkaline_phosphotase': 'Alkaline_Phosphotase',
        'alamine_aminotransferase': 'Alamine_Aminotransferase',
        'aspartate_aminotransferase': 'Aspartate_Aminotransferase',
        'total_proteins': 'Total_Proteins', 'albumin': 'Albumin',
        'albumin_and_globulin_ratio': 'Albumin_and_Globulin_Ratio'
    }
    df = df.rename(columns=column_mapping)

    # Log Transform Skewed Features
    skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
    skewed = [c for c in skewed if c in df.columns]
    df[skewed] = np.log1p(df[skewed])

    # 3. CRITICAL: Train/Test Split BEFORE Upsampling (Prevent Leakage)
    X = df.drop('target', axis=1)
    Y = df['target']

    X_train_raw, X_test, Y_train_raw, Y_test = train_test_split(X, Y, test_size=0.2, random_state=123, stratify=Y)

    print(f"Initial Split: Train={len(X_train_raw)}, Test={len(X_test)}")

    # 4. Scaling
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train_raw)
    X_test_scaled = scaler.transform(X_test)

    # Save Scaler
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"Scaler Saved to {SCALER_PATH}")

    # 5. Upsampling (Only on Training Data)
    train_df = pd.DataFrame(X_train_scaled, columns=X.columns)
    train_df['target'] = Y_train_raw.values

    minority = train_df[train_df.target == 1]
    majority = train_df[train_df.target == 0]

    if len(minority) > 0 and len(majority) > 0:
        if len(minority) < len(majority):
            minority_upsample = resample(minority, replace=True, n_samples=len(majority), random_state=42)
            train_df_balanced = pd.concat([minority_upsample, majority], axis=0)
        else:
            train_df_balanced = train_df
    else:
        train_df_balanced = train_df

    X_train_final = train_df_balanced.drop('target', axis=1)
    Y_train_final = train_df_balanced['target']

    print(f"Balanced Training Set: {len(X_train_final)} records")

    # 6. Training (XGBoost)
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        eval_metric='logloss',
        random_state=123
    )
    model.fit(X_train_final, Y_train_final)

    # 7. Evaluation
    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(Y_test, y_pred)
    print(f"Model Trained. Honest Accuracy: {acc:.4f}")

    # 8. Save Model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model Saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_liver_model()
