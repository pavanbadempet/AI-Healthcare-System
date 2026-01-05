
import os
import pickle

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "heart.parquet")
MODEL_PATH = os.path.join(BASE_DIR, "Heart Disease Model.pkl")

def train_heart_model():
    print("Starting Heart Disease Model Training...")

    import pandas as pd
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    try:
        import xgboost as xgb
    except ImportError:
        raise RuntimeError("xgboost is required to train the heart model. Install it or mock it in tests.")

    # 1. Load Data
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    df = pd.read_parquet(DATASET_PATH)
    print(f"Loaded Dataset: {len(df)} records")

    # 2. Preprocessing
    # Heart dataset is mostly numerical/categorical encoded already.
    # Notebook analysis showed no complex preprocessing or scaling was used for the final model.
    
    # 3. Features & Target
    X = df.drop(columns='target', axis=1)
    Y = df['target']

    # 4. Train/Test Split
    # Notebook used test_size=0.2, stratify=Y, random_state=2
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, stratify=Y, random_state=2)

    # 5. Training (XGBoost)
    # Using default parameters as base, or the best params found if grid search was definitive.
    # Notebook ended with: n_estimators=100, learning_rate=0.1, max_depth=5 etc.
    # We will use a robust configuration closer to the notebook's best result.
    model = xgb.XGBClassifier(
        n_estimators=100, 
        learning_rate=0.1, 
        max_depth=5, 
        subsample=0.4, 
        colsample_bytree=0.6, 
        gamma=0, 
        reg_alpha=0.1, 
        reg_lambda=0.7,
        eval_metric='logloss',
        random_state=42
    )
    model.fit(X_train, Y_train)

    # 6. Evaluation
    y_train_pred = model.predict(X_train)
    training_data_accuracy = accuracy_score(y_train_pred, Y_train)
    print('Accuracy on Training data : ', training_data_accuracy)

    y_test_pred = model.predict(X_test)
    test_data_accuracy = accuracy_score(y_test_pred, Y_test)
    print('Accuracy on Test data : ', test_data_accuracy)

    # 7. Save Model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model Saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_heart_model()
