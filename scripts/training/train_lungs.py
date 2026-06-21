import os
import pickle
import sys

# Ensure parent directory is in python path so backend is importable as package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
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
    from backend.features import LUNG_FEATURES
except ImportError:
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

    # 3. Fit Iterative Imputer (MICE with ExtraTreesRegressor)
    from sklearn.experimental import enable_iterative_imputer  # noqa
    from sklearn.impute import IterativeImputer
    from sklearn.ensemble import ExtraTreesRegressor
    imputer = IterativeImputer(
        estimator=ExtraTreesRegressor(n_estimators=10, random_state=42),
        random_state=42,
        max_iter=10
    )

    # 4. Train/Test Split
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

    X_train_imputed = imputer.fit_transform(X_train)
    X_test_imputed = imputer.transform(X_test)

    # 5. Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    X_test_scaled = scaler.transform(X_test_imputed)

    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"Scaler Saved to {SCALER_PATH}")

    # 6. Training with TabPFN (with Ensemble fallback)
    from dotenv import load_dotenv
    load_dotenv()

    token = os.environ.get("TABPFN_TOKEN")
    trained_tabpfn = False

    if token:
        print("Training TabPFN Classifier...")
        try:
            os.environ["TABPFN_TOKEN"] = token
            from tabpfn import TabPFNClassifier
            model = TabPFNClassifier(device='cpu')
            model.fit(X_train_scaled, Y_train)
            print("TabPFN Classifier trained successfully!")
            trained_tabpfn = True
        except Exception as e:
            print(f"[WARNING] TabPFN initialization/training failed: {e}")

    if not trained_tabpfn:
        if not token:
            print("[INFO] No TABPFN_TOKEN found in environment. Bypassing TabPFN to run offline.")
            print("To enable TabPFN, run 'python scripts/setup_tabpfn.py' to configure your API key.")
        print("Falling back to PyTorch Tabular Deep MLP Classifier...")
        try:
            from backend.ml.pytorch_models import PyTorchTabularMLP
        except ImportError:
            try:
                from ml.pytorch_models import PyTorchTabularMLP
            except ImportError:
                from .ml.pytorch_models import PyTorchTabularMLP

        model = PyTorchTabularMLP(hidden_dims=[64, 32], lr=0.005, epochs=150)
        model.fit(X_train_scaled, Y_train)

    # 7. Conformal Prediction Threshold (95% Confidence) - Class-Conditional
    y_proba = model.predict_proba(X_test_scaled)
    Y_test_vals = Y_test.values if hasattr(Y_test, 'values') else Y_test

    conformal_q = {}
    alpha = 0.05
    for c in [0, 1]:
        class_indices = [i for i, val in enumerate(Y_test_vals) if int(val) == c]
        if len(class_indices) > 0:
            true_class_probs_c = [y_proba[i][c] for i in class_indices]
            non_conformity_scores_c = [1.0 - p for p in true_class_probs_c]
            n_c = len(non_conformity_scores_c)
            quantile_val_c = min(1.0, max(0.0, (1.0 - alpha) * (n_c + 1) / n_c))
            q_c = float(np.quantile(non_conformity_scores_c, quantile_val_c))
            conformal_q[c] = q_c
        else:
            conformal_q[c] = 0.0
    print(f"Class-Conditional Conformal Prediction thresholds calculated: {conformal_q}")

    # 8. Evaluation
    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(Y_test, y_pred)
    print(f"Model Trained. Accuracy: {acc:.4f}")

    # Run comprehensive evaluation and save JSON artifact
    evaluate_and_save(model, X_test_scaled, Y_test, LUNG_FEATURES, "lungs")

    # 9. Save Model
    import datetime
    model_data = {
        "model": model,
        "imputer": imputer,
        "conformal_q": conformal_q,
        "model_version": "2.1.0-extratrees",
        "training_timestamp": datetime.datetime.now().isoformat(),
        "model_card_id": "card-lungs-v2"
    }
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    print(f"Model Saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_lungs_model()
