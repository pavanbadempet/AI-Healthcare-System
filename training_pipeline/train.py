import mlflow
import mlflow.xgboost
import xgboost as xgb
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Configuration
DATA_PATH = "data/processed/test_data.parquet"
MODEL_NAME = "diabetes_model"

def train_model():
    print(f"Loading data from {DATA_PATH}...")
    
    if not os.path.exists(DATA_PATH):
        print("Data not found. Please run 'data_pipeline/01_ingest.py' first.")
        return

    df = pd.read_parquet(DATA_PATH)
    
    # Prepare Features/Target (Based on our Dummy Data)
    # Warning: specific columns depend on the data schema
    target_col = "diabetes"
    
    if target_col not in df.columns:
        print(f"Target column '{target_col}' not found. Cannot train.")
        return

    X = df.drop(columns=[target_col, "gender", "smoking_history"]) # Drop text for now or encode
    y = df[target_col]

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Enable MLflow Autologging
    mlflow.xgboost.autolog()

    print("Starting MLflow Run...")
    with mlflow.start_run():
        # Train
        model = xgb.XGBClassifier(use_label_encoder=False, eval_metric="logloss")
        model.fit(X_train, y_train)

        # Evaluate
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        print(f"Model Accuracy: {acc}")
        
        # Log custom metric if needed
        mlflow.log_metric("custom_accuracy", acc)
        
        # Manually Log Model (optional, autolog usually handles it)
        # mlflow.xgboost.log_model(model, "model")
        
        print(f"Training Complete. Model logged to MLflow Run ID: {mlflow.active_run().info.run_id}")

if __name__ == "__main__":
    train_model()
