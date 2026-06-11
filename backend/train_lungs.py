import os
import pickle

import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

try:
    from backend.ml.evaluation import evaluate_and_save
except ImportError:
    try:
        from ml.evaluation import evaluate_and_save
    except ImportError:
        from evaluation import evaluate_and_save

try:
    from .features import LUNG_FEATURES
except ImportError:
    from features import LUNG_FEATURES

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "lungs.parquet")
MODEL_PATH = os.path.join(BASE_DIR, "lungs_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "lungs_scaler.pkl")

def train_lungs_model():
    print("Starting Lungs Health Model Training...")

    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    df = pd.read_parquet(DATASET_PATH)
    print(f"Loaded Dataset: {len(df)} records")

    # 2. Features & Target
    # Features as expected by prediction.py (UPPERCASE)
    X = df[LUNG_FEATURES]
    Y = df["target"]

    # 3. Scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"Scaler Saved to {SCALER_PATH}")

    # 4. Train/Test Split
    X_train, X_test, Y_train, Y_test = train_test_split(X_scaled, Y, test_size=0.2, random_state=42)

    # 5. Training
    neg_count = int((Y_train == 0).sum())
    pos_count = int((Y_train == 1).sum())
    scale_weight = neg_count / pos_count if pos_count > 0 else 1.0
    print(f"Class balance: neg={neg_count}, pos={pos_count}, scale_pos_weight={scale_weight:.2f}")

    model = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=4,
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

    # 6. Evaluation
    y_pred = model.predict(X_test)
    acc = accuracy_score(Y_test, y_pred)
    print(f"Model Trained. Accuracy: {acc:.4f}")

    # Run comprehensive evaluation and save JSON artifact
    evaluate_and_save(model, X_test, Y_test, LUNG_FEATURES, "lungs")

    # 7. Save Model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model Saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_lungs_model()
