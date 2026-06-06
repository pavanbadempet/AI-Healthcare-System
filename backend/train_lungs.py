import os
import pickle

import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

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
    model = xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, eval_metric='logloss')
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
    train_lungs_model()
