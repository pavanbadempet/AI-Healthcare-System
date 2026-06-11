import os
import pickle

import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

try:
    from backend.ml.evaluation import evaluate_and_save
except ImportError:
    try:
        from ml.evaluation import evaluate_and_save
    except ImportError:
        from evaluation import evaluate_and_save

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "diabetes.parquet")
MODEL_PATH = os.path.join(BASE_DIR, "diabetes_model.pkl")

def train_diabetes_model():
    print("Starting Diabetes Model Training (BRFSS 2015)...")

    # 1. Load Data
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    df = pd.read_parquet(DATASET_PATH)
    print(f"Loaded Dataset: {len(df)} records")

    # 2. Features & Target
    try:
        from .features import DIABETES_DATASET_MAP, DIABETES_FEATURES
    except ImportError:
        from features import DIABETES_DATASET_MAP, DIABETES_FEATURES

    # Check if we need to rename columns
    if all(col in df.columns for col in DIABETES_DATASET_MAP.keys()):
        print("Renaming columns to canonical names...")
        df = df.rename(columns=DIABETES_DATASET_MAP)

    # Select only required features
    X = df[DIABETES_FEATURES]
    Y = df["diabetes"]

    print(f"Features: {X.columns.tolist()}")

    # 3. Train/Test Split
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

    # 4. Training (XGBoost with class balancing)
    neg_count = int((Y_train == 0).sum())
    pos_count = int((Y_train == 1).sum()) + int((Y_train == 2).sum())
    scale_weight = neg_count / pos_count if pos_count > 0 else 1.0
    print(f"Class balance: neg={neg_count}, pos={pos_count}, scale_pos_weight={scale_weight:.2f}")

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        scale_pos_weight=scale_weight,
        eval_metric='logloss',
        random_state=42
    )
    model.fit(X_train, Y_train)

    # 5. Evaluation
    y_pred = model.predict(X_test)
    acc = accuracy_score(Y_test, y_pred)
    print(f"Model Trained. Accuracy: {acc:.4f}")

    # Run comprehensive evaluation and save JSON artifact
    evaluate_and_save(model, X_test, Y_test, DIABETES_FEATURES, "diabetes")

    # 6. Save Model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model Saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_diabetes_model()
