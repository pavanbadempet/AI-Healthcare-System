"""
AI Healthcare System - Training Pipeline
"""

import sys
import os
import pickle
import pandas as pd
import numpy as np
import logging
from sklearn.model_selection import train_test_split
from sklearn.ensemble import VotingClassifier, RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

# --- Logging Configuration (Standardized) ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('training.log')
    ]
)
logger = logging.getLogger(__name__)

DATA_DIR = 'data'
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
# Robust Path: Resolves to project_root/models regardless of where script is run
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')

# --- SOTA Hyperparameters (Targeting 80%+) ---
xgb_params = {'n_estimators': 500, 'max_depth': 6, 'learning_rate': 0.03, 'eval_metric': 'logloss', 'random_state': 42, 'tree_method': 'hist'}
rf_params = {'n_estimators': 500, 'max_depth': 12, 'random_state': 42, 'n_jobs': -1} # Parallel RF
gb_params = {'n_estimators': 300, 'learning_rate': 0.05, 'max_depth': 5, 'random_state': 42}
lgbm_params = {'n_estimators': 500, 'learning_rate': 0.03, 'num_leaves': 31, 'random_state': 42}
cat_params = {'iterations': 500, 'learning_rate': 0.03, 'depth': 6, 'verbose': False, 'random_state': 42}

def train_diabetes():
    logger.info("Training Diabetes Ensemble (Big Data - BRFSS)...")
    parquet_path = os.path.join(PROCESSED_DIR, 'diabetes.parquet')
    if not os.path.exists(parquet_path): return

    df = pd.read_parquet(parquet_path)
    target = 'diabetes'
    
    # Select only the features available in the Web UI/API
    # Mapped from original: HighBP, HighChol, BMI, Smoker, HeartDiseaseorAttack, PhysActivity, GenHlth, Sex, Age
    feature_cols = ['HighBP', 'HighChol', 'BMI', 'Smoker', 'HeartDiseaseorAttack', 'PhysActivity', 'GenHlth', 'Sex', 'Age']
    
    X = df[feature_cols]
    y = df[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    eclf = VotingClassifier(estimators=[
        ('xgb', XGBClassifier(**xgb_params)), 
        ('rf', RandomForestClassifier(**rf_params)), 
        ('gb', GradientBoostingClassifier(**gb_params))
    ], voting='soft')
    eclf.fit(X_train, y_train)
    
    acc = accuracy_score(y_test, eclf.predict(X_test))
    logger.info(f"[Diabetes] Accuracy: {acc:.4f}")
    with open(os.path.join(MODEL_DIR, 'diabetes_model.pkl'), 'wb') as f: pickle.dump(eclf, f)

def train_heart():
    logger.info("Training Heart Ensemble (CDC BRFSS - 250k Rows)...")
    parquet_path = os.path.join(PROCESSED_DIR, 'heart.parquet')
    if not os.path.exists(parquet_path): return

    df = pd.read_parquet(parquet_path)
    # Schema: target, high_bp, high_chol, bmi, smoker, stroke, diabetes, phys_activity, hvy_alcohol, gen_hlth, sex, age
    # No clinical cleaning needed as BRFSS is already cleaned/categorical.
    
    target = 'target'
    X = df.drop(columns=[target])
    y = df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. SOTA Ensemble for Large Categorical Data
    # LightGBM is King here.
    eclf = VotingClassifier(estimators=[
        ('xgb', XGBClassifier(**xgb_params)), 
        ('rf', RandomForestClassifier(**rf_params)), 
        ('lgbm', LGBMClassifier(**lgbm_params))
    ], voting='soft')
    
    eclf.fit(X_train, y_train)

    acc = accuracy_score(y_test, eclf.predict(X_test))
    logger.info(f"[Heart] CDC Ensemble Accuracy: {acc:.4f}")

    with open(os.path.join(MODEL_DIR, 'heart_disease_model.pkl'), 'wb') as f:
        pickle.dump(eclf, f)

def train_liver():
    logger.info("Training Liver Ensemble...")
    parquet_path = os.path.join(PROCESSED_DIR, 'liver.parquet')
    if not os.path.exists(parquet_path): return

    df = pd.read_parquet(parquet_path)
    target = 'target'
    skewed = ['total_bilirubin', 'alkaline_phosphotase', 'alamine_aminotransferase', 'albumin_and_globulin_ratio']
    skewed = [c for c in skewed if c in df.columns]
    for col in skewed: df[col] = np.log1p(df[col])

    scaler = StandardScaler()
    feature_cols = [c for c in df.columns if c != target]
    X = df[feature_cols]
    y = df[target]
    X_scaled = scaler.fit_transform(X)
    
    with open(os.path.join(MODEL_DIR, 'scaler.pkl'), 'wb') as f: pickle.dump(scaler, f)
    
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    eclf = VotingClassifier(estimators=[
        ('xgb', XGBClassifier(**xgb_params)), 
        ('rf', RandomForestClassifier(**rf_params)), 
        ('gb', GradientBoostingClassifier(**gb_params))
    ], voting='soft')
    eclf.fit(X_train, y_train)
    acc = accuracy_score(y_test, eclf.predict(X_test))
    logger.info(f"[Liver] Accuracy: {acc:.4f}")
    with open(os.path.join(MODEL_DIR, 'liver_disease_model.pkl'), 'wb') as f: pickle.dump(eclf, f)

def train_kidney():
    logger.info("Training Kidney Model (XGBoost - User Requested)...")
    parquet_path = os.path.join(PROCESSED_DIR, 'kidney.parquet')
    if not os.path.exists(parquet_path): return

    df = pd.read_parquet(parquet_path)
    if 'classification' in df.columns: df.drop(columns=['classification'], inplace=True)
    target = 'target'
    
    X = df.drop(columns=[target])
    y = df[target]
    
    # Scale because some values (WBC) are large
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    with open(os.path.join(MODEL_DIR, 'kidney_scaler.pkl'), 'wb') as f: pickle.dump(scaler, f)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # XGBoost Only (User Request)
    model = XGBClassifier(
        n_estimators=200, 
        max_depth=4, 
        learning_rate=0.05, 
        eval_metric='logloss',
        random_state=42
    )
    model.fit(X_train, y_train)
    
    acc = accuracy_score(y_test, model.predict(X_test))
    logger.info(f"[Kidney] XGBoost Accuracy: {acc:.4f}")
    
    with open(os.path.join(MODEL_DIR, 'kidney_model.pkl'), 'wb') as f: pickle.dump(model, f)

def train_lungs():
    logger.info("Training Lung Health Model (XGBoost)...")
    parquet_path = os.path.join(PROCESSED_DIR, 'lungs.parquet')
    if not os.path.exists(parquet_path): return

    df = pd.read_parquet(parquet_path)
    target = 'target'
    
    X = df.drop(columns=[target])
    y = df[target]
    
    # 0/1 Scaling (MinMax is fine or Standard)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    with open(os.path.join(MODEL_DIR, 'lungs_scaler.pkl'), 'wb') as f: pickle.dump(scaler, f)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    model = XGBClassifier(
        n_estimators=100, 
        max_depth=3, 
        learning_rate=0.05, 
        eval_metric='logloss',
        random_state=42
    )
    model.fit(X_train, y_train)
    
    acc = accuracy_score(y_test, model.predict(X_test))
    logger.info(f"[Lungs] XGBoost Accuracy: {acc:.4f}")
    
    with open(os.path.join(MODEL_DIR, 'lungs_model.pkl'), 'wb') as f: pickle.dump(model, f)

if __name__ == "__main__":
    train_diabetes() 
    train_heart() 
    train_liver() 
    train_kidney()
    train_lungs()
