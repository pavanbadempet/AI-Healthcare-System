
import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
import os
from sklearn.preprocessing import LabelEncoder, RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.utils import resample
from sklearn.metrics import accuracy_score

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "..", "data", "raw", "liver_large.csv")
MODEL_PATH = os.path.join(BASE_DIR, "Liver Disease Model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "LiverScaler.pkl")

def train_liver_model():
    print("Starting Liver Disease Model Training...")

    # 1. Load Data
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    df = pd.read_csv(DATASET_PATH, encoding='latin-1')
    print(f"Loaded Dataset: {len(df)} records")

    # Rename Columns
    df = df.rename(columns={
        "Age of the patient": "Age",
        "Gender of the patient": "Gender", 
        "Total Bilirubin": "Total_Bilirubin",
        "Direct Bilirubin": "Direct_Bilirubin",
        "\xa0Alkphos Alkaline Phosphotase": "Alkaline_Phosphotase",
        "\xa0Sgpt Alamine Aminotransferase": "Alamine_Aminotransferase",
        "Sgot Aspartate Aminotransferase": "Aspartate_Aminotransferase",
        "Total Protiens": "Total_Proteins",
        "\xa0ALB Albumin": "Albumin",
        "A/G Ratio Albumin and Globulin Ratio": "Albumin_and_Globulin_Ratio",
        "Result": "Dataset"
    })
    
    # Handle weird encoding char explicitly if needed
    df.columns = df.columns.str.replace('', '').str.strip()
    # Re-apply explicit rename for safety if encoding strip worked differently
    df = df.rename(columns={
        "Alkphos Alkaline Phosphotase": "Alkaline_Phosphotase",
        "Sgpt Alamine Aminotransferase": "Alamine_Aminotransferase",
        "ALB Albumin": "Albumin"
    })

    # 2. Preprocessing
    
    # 2a. Handle Missing Values
    # Notebook filled 'Albumin_and_Globulin_Ratio' with mean.
    df['Albumin_and_Globulin_Ratio'].fillna(df['Albumin_and_Globulin_Ratio'].mean(), inplace=True)

    # 2b. Gender Encoding
    # Notebook: Male->1, Female->0 (via LabelEncoder)
    le = LabelEncoder()
    df['Gender'] = le.fit_transform(df['Gender'])

    # 2c. Log Transform Skewed Features
    # Notebook logic: np.log1p applied to skewed columns
    skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
    df[skewed] = np.log1p(df[skewed])

    # 2d. Scaling (RobustScaler)
    # Fit scaler on features (excluding Dataset)
    # The scaler must be fitted BEFORE splitting/upsampling to maintain distribution validity, 
    # OR fitted on training split. Notebook scaled EVERYTHING before upsampling.
    # We will follow the notebook pattern to ensure close reproduction, but typically we split first.
    # Notebook: rs.fit_transform(liver_data[attributes])
    
    attributes = [col for col in df.columns if col != 'Dataset']
    scaler = RobustScaler()
    df[attributes] = scaler.fit_transform(df[attributes])
    
    # Save Scaler (CRITICAL: Save as LiverScaler.pkl)
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"Scaler Saved to {SCALER_PATH}")

    # 2e. Upsampling
    # Notebook split by Dataset: 1 (Majority), 2 (Minority)
    # Then upsampled minority to match majority size.
    minority = df[df.Dataset==2]
    majority = df[df.Dataset==1]
    
    minority_upsample = resample(minority, replace=True, n_samples=len(majority), random_state=42)
    df_upsampled = pd.concat([minority_upsample, majority], axis=0)

    # 2f. Target Mapping
    # Notebook maps: 2->0 (Healthy), 1->1 (Disease)
    df_upsampled['Dataset'] = df_upsampled['Dataset'].map({2: 0, 1: 1})

    # 3. Train/Test Split
    X = df_upsampled.drop('Dataset', axis=1)
    Y = df_upsampled['Dataset']
    
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
