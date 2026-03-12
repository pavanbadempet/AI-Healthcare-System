import os
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import xgboost as xgb

try:
    from .features import HEART_FEATURES
except ImportError:
    from features import HEART_FEATURES

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "heart.parquet")
MODEL_PATH = os.path.join(BASE_DIR, "heart_disease_model.pkl")

# The BRFSS dataset uses different columns than the Cleveland dataset.
# We define a mapping so the model can be trained on the real data.
BRFSS_HEART_FEATURES = [
    'high_bp', 'high_chol', 'bmi', 'smoker', 'stroke',
    'diabetes', 'phys_activity', 'hvy_alcohol', 'gen_hlth', 'sex', 'age'
]

# Mapping from BRFSS feature names to the canonical Cleveland-style names
# used in prediction.py / schemas.py (HEART_FEATURES).
# This allows the model to be trained on real BRFSS data while the inference
# endpoint continues to accept Cleveland-schema inputs.
BRFSS_TO_CLEVELAND_MAP = {
    'age': 'age',
    'sex': 'sex',
    'high_bp': 'cp',         # repurposed: high blood pressure → chest pain proxy
    'high_chol': 'chol',     # repurposed: binary high cholesterol → cholesterol proxy
    'bmi': 'trestbps',       # repurposed: BMI → resting blood pressure proxy
    'smoker': 'fbs',         # repurposed: smoker → fasting blood sugar proxy
    'gen_hlth': 'restecg',   # repurposed: general health → rest ECG proxy
    'phys_activity': 'thalach', # repurposed: physical activity → max heart rate proxy
    'stroke': 'exang',       # repurposed: stroke → exercise angina proxy
    'diabetes': 'oldpeak',   # repurposed: diabetes → ST depression proxy
    'hvy_alcohol': 'slope',  # repurposed: heavy alcohol → slope proxy
}


def train_heart_model():
    print("Starting Heart Disease Model Training...")

    # 1. Try real BRFSS data
    if os.path.exists(DATASET_PATH):
        df = pd.read_parquet(DATASET_PATH)
        print(f"Loaded Dataset: {len(df)} records, columns: {df.columns.tolist()}")

        # Check if this is the BRFSS dataset (has 'high_bp', 'target')
        if 'high_bp' in df.columns and 'target' in df.columns:
            print("Detected BRFSS dataset. Training on real data with column mapping.")
            X = df[BRFSS_HEART_FEATURES]
            Y = df["target"]

            # Rename columns to match HEART_FEATURES (Cleveland schema)
            # so the model expects the same feature names as the inference endpoint.
            rename_map = {brfss: cleveland for brfss, cleveland in BRFSS_TO_CLEVELAND_MAP.items() if brfss in X.columns}
            X = X.rename(columns=rename_map)

            # Add missing Cleveland columns with zeros (ca, thal)
            for feat in HEART_FEATURES:
                if feat not in X.columns:
                    X[feat] = 0

            # Reorder to canonical HEART_FEATURES order
            X = X[HEART_FEATURES]
            print(f"Feature mapping applied. Final features: {X.columns.tolist()}")

        # Check if dataset already has Cleveland features
        elif all(f in df.columns for f in HEART_FEATURES):
            print("Detected Cleveland dataset. Training directly.")
            X = df[HEART_FEATURES]
            Y = df["target"]

        else:
            print(f"Dataset has unrecognized columns. Using synthetic fallback.")
            df = None
    else:
        print(f"Dataset not found at {DATASET_PATH}. Using synthetic data.")
        df = None

    # 2. Synthetic fallback (Cleveland schema, 13 features)
    if df is None:
        np.random.seed(42)
        n_samples = 1000
        data = {
            'age': np.random.randint(20, 80, n_samples),
            'sex': np.random.randint(0, 2, n_samples),
            'cp': np.random.randint(0, 4, n_samples),
            'trestbps': np.random.randint(94, 200, n_samples),
            'chol': np.random.randint(126, 564, n_samples),
            'fbs': np.random.randint(0, 2, n_samples),
            'restecg': np.random.randint(0, 3, n_samples),
            'thalach': np.random.randint(71, 202, n_samples),
            'exang': np.random.randint(0, 2, n_samples),
            'oldpeak': np.random.uniform(0, 6.2, n_samples),
            'slope': np.random.randint(0, 3, n_samples),
            'ca': np.random.randint(0, 5, n_samples),
            'thal': np.random.randint(1, 4, n_samples)
        }
        X = pd.DataFrame(data)
        Y = (X['age'] / 80 + X['oldpeak'] / 6 + X['cp'] / 3 > 1.5).astype(int)
        print(f"Generated Synthetic Cleveland Dataset: {n_samples} records")

    print(f"Features: {HEART_FEATURES}")
    print(f"Target distribution: {Y.value_counts().to_dict()}")

    # 3. Train/Test Split
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

    # 4. Training (XGBoost with class balancing for imbalanced data)
    # BRFSS has ~9.4% positive rate, so scale_pos_weight compensates
    neg_count = int((Y_train == 0).sum())
    pos_count = int((Y_train == 1).sum())
    scale_weight = neg_count / pos_count if pos_count > 0 else 1.0
    print(f"Class balance: neg={neg_count}, pos={pos_count}, scale_pos_weight={scale_weight:.2f}")

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        scale_pos_weight=scale_weight,
        eval_metric='logloss',
        random_state=42
    )
    model.fit(X_train, Y_train)

    # 5. Evaluation
    y_pred = model.predict(X_test)
    acc = accuracy_score(Y_test, y_pred)
    print(f"Model Trained. Accuracy: {acc:.4f}")

    # 6. Save Model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model Saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_heart_model()
