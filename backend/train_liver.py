
import os
import pickle

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "liver.parquet")
MODEL_PATH = os.path.join(BASE_DIR, "Liver Disease Model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "LiverScaler.pkl")

def train_liver_model():
    print("Starting Liver Disease Model Training...")
    
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import LabelEncoder, RobustScaler
    from sklearn.model_selection import train_test_split
    from sklearn.utils import resample
    from sklearn.metrics import accuracy_score
    try:
        import xgboost as xgb
    except ImportError:
        raise RuntimeError("xgboost is required to train the liver model. Install it or mock it in tests.")

    # 1. Load Data
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    df = pd.read_parquet(DATASET_PATH)
    print(f"Loaded Dataset: {len(df)} records")

    # 2. Preprocessing
    # Data is already cleaned and encoded in Parquet (columns are lowercase snake_case)
    # Mapping: age, gender, total_bilirubin, direct_bilirubin, alkaline_phosphotase, 
    # alamine_aminotransferase, aspartate_aminotransferase, total_proteins, albumin, 
    # albumin_and_globulin_ratio, target

    # 2c. Log Transform Skewed Features
    # Note: Column names are now lowercase
    skewed = ['total_bilirubin', 'alkaline_phosphotase', 'alamine_aminotransferase', 'albumin_and_globulin_ratio']
    # Ensure columns exist before transforming
    skewed = [c for c in skewed if c in df.columns]
    df[skewed] = np.log1p(df[skewed])

    # 2d. Scaling (RobustScaler)
    attributes = [col for col in df.columns if col != 'target']
    scaler = RobustScaler()
    df[attributes] = scaler.fit_transform(df[attributes])
    
    # Save Scaler
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"Scaler Saved to {SCALER_PATH}")

    # 2e. Upsampling
    # Target is 'target' (0/1)
    minority = df[df.target==1] # Assuming 1 is minority/disease
    majority = df[df.target==0]
    
    # Check which is actually minority
    if len(minority) > len(majority):
        minority, majority = majority, minority

    minority_upsample = resample(minority, replace=True, n_samples=len(majority), random_state=42)
    df_upsampled = pd.concat([minority_upsample, majority], axis=0)

    # 3. Train/Test Split
    X = df_upsampled.drop('target', axis=1)
    Y = df_upsampled['target']
    
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.25, random_state=123)

    # 4. Training (XGBoost)
    # Notebook best params: {'n_estimators': 500, 'learning_rate': 0.1, ...}
    # Simplified here to a robust base configuration or matching notebook.
    model = xgb.XGBClassifier(
        n_estimators=500,
        learning_rate=0.1,
        max_depth=5,
        gamma=0,
        reg_alpha=0,
        reg_lambda=1,
        random_state=123,
        eval_metric='logloss'
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
    train_liver_model()
