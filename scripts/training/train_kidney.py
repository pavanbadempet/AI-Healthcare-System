import os
import pickle

import numpy as np
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
    from backend.features import KIDNEY_FEATURES
except ImportError:
    try:
        from .features import KIDNEY_FEATURES
    except ImportError:
        from features import KIDNEY_FEATURES

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "kidney.parquet")
MODEL_PATH = os.path.join(BASE_DIR, "kidney_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "kidney_scaler.pkl")

def train_kidney_model():
    print("Starting Kidney Disease Model Training...")

    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    df = pd.read_parquet(DATASET_PATH)
    print(f"Loaded Dataset: {len(df)} records")

    # 2. Features & Target
    # Features as expected by prediction.py
    X = df[KIDNEY_FEATURES]
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
        print("Falling back to Calibrated Soft Voting Ensemble (XGBoost + LightGBM + Random Forest)...")
        import lightgbm as lgb
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.ensemble import RandomForestClassifier, VotingClassifier

        neg_count = int((Y_train == 0).sum())
        pos_count = int((Y_train == 1).sum())
        scale_weight = neg_count / pos_count if pos_count > 0 else 1.0

        clf_xgb = xgb.XGBClassifier(
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

        clf_lgb = lgb.LGBMClassifier(
            n_estimators=150,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        )

        clf_rf = RandomForestClassifier(
            n_estimators=150,
            max_depth=6,
            random_state=42,
            class_weight="balanced"
        )

        # Robust calibration setup based on dataset size
        min_class_count = min(neg_count, pos_count)
        if min_class_count >= 5:
            calibrated_xgb = CalibratedClassifierCV(estimator=clf_xgb, cv=5, method='sigmoid')
            calibrated_lgb = CalibratedClassifierCV(estimator=clf_lgb, cv=5, method='sigmoid')
            calibrated_rf = CalibratedClassifierCV(estimator=clf_rf, cv=5, method='sigmoid')
        elif min_class_count >= 2:
            calibrated_xgb = CalibratedClassifierCV(estimator=clf_xgb, cv=min_class_count, method='sigmoid')
            calibrated_lgb = CalibratedClassifierCV(estimator=clf_lgb, cv=min_class_count, method='sigmoid')
            calibrated_rf = CalibratedClassifierCV(estimator=clf_rf, cv=min_class_count, method='sigmoid')
        else:
            calibrated_xgb = clf_xgb
            calibrated_lgb = clf_lgb
            calibrated_rf = clf_rf

        model = VotingClassifier(
            estimators=[
                ('xgb', calibrated_xgb),
                ('lgb', calibrated_lgb),
                ('rf', calibrated_rf)
            ],
            voting='soft'
        )
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
    evaluate_and_save(model, X_test_scaled, Y_test, KIDNEY_FEATURES, "kidney")

    # 9. Save Model
    import datetime
    model_data = {
        "model": model,
        "imputer": imputer,
        "conformal_q": conformal_q,
        "model_version": "2.1.0-extratrees",
        "training_timestamp": datetime.datetime.now().isoformat(),
        "model_card_id": "card-kidney-v2"
    }
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    print(f"Model Saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_kidney_model()
