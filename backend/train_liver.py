import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pickle

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.utils import resample

try:
    from backend.ml.evaluation import evaluate_and_save
except ImportError:
    try:
        from ml.evaluation import evaluate_and_save
    except ImportError:
        from evaluation import evaluate_and_save

try:
    from backend.features import LIVER_FEATURES
except ImportError:
    try:
        from features import LIVER_FEATURES
    except ImportError:
        from .features import LIVER_FEATURES

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

    X_train_raw, X_test_raw, Y_train_raw, Y_test = train_test_split(X, Y, test_size=0.2, random_state=123, stratify=Y)

    print(f"Initial Split: Train={len(X_train_raw)}, Test={len(X_test_raw)}")

    # 3. Fit Iterative Imputer (MICE with ExtraTreesRegressor)
    from sklearn.experimental import enable_iterative_imputer  # noqa
    from sklearn.impute import IterativeImputer
    from sklearn.ensemble import ExtraTreesRegressor
    imputer = IterativeImputer(
        estimator=ExtraTreesRegressor(n_estimators=10, random_state=42),
        random_state=42,
        max_iter=10
    )
    X_train_imputed = imputer.fit_transform(X_train_raw)
    X_test_imputed = imputer.transform(X_test_raw)

    # 4. Scaling
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    X_test_scaled = scaler.transform(X_test_imputed)

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
            model.fit(X_train_final, Y_train_final)
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

        clf_xgb = xgb.XGBClassifier(
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

        clf_lgb = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=123,
            verbose=-1
        )

        clf_rf = RandomForestClassifier(
            n_estimators=150,
            max_depth=6,
            random_state=123,
            class_weight="balanced"
        )

        # Robust calibration setup based on dataset size
        neg_count = int((Y_train_final == 0).sum())
        pos_count = int((Y_train_final == 1).sum())
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

        clf_mlp = PyTorchTabularMLP(hidden_dims=[64, 32], lr=0.005, epochs=30, batch_size=512, dropout=0.1)
        clf_ftt = FTTransformerClassifier(d_embedding=16, n_heads=2, depth=2, ffn_dropout=0.1, lr=0.005, epochs=10, batch_size=512)

        # Robust calibration setup based on dataset size
        min_class_count = min(neg_count, pos_count)
        if min_class_count >= 5:
            calibrated_xgb = CalibratedClassifierCV(estimator=clf_xgb, cv=5, method='sigmoid')
            calibrated_lgb = CalibratedClassifierCV(estimator=clf_lgb, cv=5, method='sigmoid')
            calibrated_rf = CalibratedClassifierCV(estimator=clf_rf, cv=5, method='sigmoid')
            calibrated_mlp = CalibratedClassifierCV(estimator=clf_mlp, cv=5, method='sigmoid')
            calibrated_ftt = CalibratedClassifierCV(estimator=clf_ftt, cv=3, method='sigmoid')
        elif min_class_count >= 2:
            calibrated_xgb = CalibratedClassifierCV(estimator=clf_xgb, cv=min_class_count, method='sigmoid')
            calibrated_lgb = CalibratedClassifierCV(estimator=clf_lgb, cv=min_class_count, method='sigmoid')
            calibrated_rf = CalibratedClassifierCV(estimator=clf_rf, cv=min_class_count, method='sigmoid')
            calibrated_mlp = CalibratedClassifierCV(estimator=clf_mlp, cv=min_class_count, method='sigmoid')
            calibrated_ftt = CalibratedClassifierCV(estimator=clf_ftt, cv=min(3, min_class_count), method='sigmoid')
        else:
            calibrated_xgb = clf_xgb
            calibrated_lgb = clf_lgb
            calibrated_rf = clf_rf
            calibrated_mlp = clf_mlp
            calibrated_ftt = clf_ftt

        model = VotingClassifier(
            estimators=[
                ('xgb', calibrated_xgb),
                ('lgb', calibrated_lgb),
                ('rf', calibrated_rf),
                ('mlp', calibrated_mlp),
                ('ftt', calibrated_ftt)
            ],
            voting='soft'
        )
        model.fit(X_train_final, Y_train_final)

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
    print(f"Model Trained. Honest Accuracy: {acc:.4f}")

    # Run comprehensive evaluation and save JSON artifact
    evaluate_and_save(model, X_test_scaled, Y_test, LIVER_FEATURES, "liver")

    # 9. Save Model
    import datetime
    model_data = {
        "model": model,
        "imputer": imputer,
        "conformal_q": conformal_q,
        "model_version": "2.1.0-extratrees",
        "training_timestamp": datetime.datetime.now().isoformat(),
        "model_card_id": "card-liver-v2"
    }
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    print(f"Model Saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_liver_model()
