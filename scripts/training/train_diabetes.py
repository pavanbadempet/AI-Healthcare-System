import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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
        from backend.features import DIABETES_DATASET_MAP, DIABETES_FEATURES
    except ImportError:
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

    # 3. Fit Iterative Imputer (MICE with ExtraTreesRegressor)
    from sklearn.experimental import enable_iterative_imputer  # noqa
    from sklearn.impute import IterativeImputer
    from sklearn.ensemble import ExtraTreesRegressor
    imputer = IterativeImputer(
        estimator=ExtraTreesRegressor(n_estimators=10, random_state=42),
        random_state=42,
        max_iter=10
    )
    X_train_imputed = imputer.fit_transform(X_train)
    X_test_imputed = imputer.transform(X_test)

    # 4. Training (Calibrated Soft Voting Quad-Ensemble: XGBoost + LightGBM + CatBoost + Random Forest)
    import catboost as cb
    import lightgbm as lgb
    import numpy as np
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.ensemble import RandomForestClassifier, VotingClassifier

    neg_count = int((Y_train == 0).sum())
    pos_count = int((Y_train == 1).sum()) + int((Y_train == 2).sum())
    scale_weight = neg_count / pos_count if pos_count > 0 else 1.0
    print(f"Class balance: neg={neg_count}, pos={pos_count}, scale_pos_weight={scale_weight:.2f}")

    clf_xgb = xgb.XGBClassifier(
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

    clf_lgb = lgb.LGBMClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbose=-1
    )

    clf_cat = cb.CatBoostClassifier(
        iterations=300,
        depth=6,
        learning_rate=0.05,
        random_seed=42,
        verbose=0
    )

    clf_rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=42,
        class_weight="balanced"
    )

    calibrated_xgb = CalibratedClassifierCV(estimator=clf_xgb, cv=5, method='sigmoid')
    calibrated_lgb = CalibratedClassifierCV(estimator=clf_lgb, cv=5, method='sigmoid')
    calibrated_cat = CalibratedClassifierCV(estimator=clf_cat, cv=5, method='sigmoid')
    calibrated_rf = CalibratedClassifierCV(estimator=clf_rf, cv=5, method='sigmoid')

    # Import and instantiate PyTorch Tabular Deep MLP
    try:
        from backend.ml.pytorch_models import PyTorchTabularMLP
    except ImportError:
        try:
            from ml.pytorch_models import PyTorchTabularMLP
        except ImportError:
            from .ml.pytorch_models import PyTorchTabularMLP

    # Import and instantiate FT-Transformer Tabular Deep Model
    try:
        from backend.ml.advanced_pytorch_models import FTTransformerClassifier
    except ImportError:
        try:
            from ml.advanced_pytorch_models import FTTransformerClassifier
        except ImportError:
            from .ml.advanced_pytorch_models import FTTransformerClassifier

    clf_mlp = PyTorchTabularMLP(hidden_dims=[64, 32], lr=0.005, epochs=15, batch_size=1024, dropout=0.1)
    calibrated_mlp = CalibratedClassifierCV(estimator=clf_mlp, cv=5, method='sigmoid')

    clf_ftt = FTTransformerClassifier(d_embedding=16, n_heads=2, depth=2, ffn_dropout=0.1, lr=0.005, epochs=5, batch_size=2048)
    calibrated_ftt = CalibratedClassifierCV(estimator=clf_ftt, cv=3, method='sigmoid')

    model = VotingClassifier(
        estimators=[
            ('xgb', calibrated_xgb),
            ('lgb', calibrated_lgb),
            ('cat', calibrated_cat),
            ('rf', calibrated_rf),
            ('mlp', calibrated_mlp),
            ('ftt', calibrated_ftt)
        ],
        voting='soft'
    )
    model.fit(X_train_imputed, Y_train)

    # 5. Conformal Prediction Threshold (95% Confidence) - Class-Conditional
    y_proba = model.predict_proba(X_test_imputed)
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

    # 6. Evaluation
    y_pred = model.predict(X_test_imputed)
    acc = accuracy_score(Y_test, y_pred)
    print(f"Model Trained. Accuracy: {acc:.4f}")

    # Run comprehensive evaluation and save JSON artifact
    evaluate_and_save(model, X_test_imputed, Y_test, DIABETES_FEATURES, "diabetes")

    # 7. Save Model with metadata dictionary
    import datetime
    model_data = {
        "model": model,
        "imputer": imputer,
        "conformal_q": conformal_q,
        "model_version": "2.1.0-extratrees",
        "training_timestamp": datetime.datetime.now().isoformat(),
        "model_card_id": "card-diabetes-v2"
    }
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    print(f"Model Saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_diabetes_model()
