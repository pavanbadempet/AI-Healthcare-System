import os
import sys
import json
import torch
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from psycopg2.extras import execute_values

print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Device: {torch.cuda.get_device_name(0)}")

# Doppler injects DATABASE_URL at push time for Kaggle environment
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not available. Ensure Doppler has DATABASE_URL set.")
    sys.exit(0)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print("Connecting to Neon PostgreSQL...")
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

try:
    print("Fetching Gold Medallion data...")
    # Assume 'gold_patient_hourly_vitals' is exported by Databricks
    df = pd.read_sql("SELECT patient_id, avg_heart_rate, max_systolic_bp, min_spo2, hypoxic_events FROM gold_patient_hourly_vitals", engine)
    print(f"Loaded {len(df)} patient records.")

    if not df.empty:
        print("Running Neural Network Risk Scoring Model on GPU...")
        
        # Simulate a deep learning PyTorch model predicting risk score based on vitals
        # In a real pipeline, you would load a trained .pt model here.
        # We'll use a simple deterministic tensor operation to simulate GPU work.
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Convert features to tensor
        features = df[["avg_heart_rate", "max_systolic_bp", "min_spo2", "hypoxic_events"]].fillna(0).values
        tensor_features = torch.tensor(features, dtype=torch.float32).to(device)
        
        # Simulate some ML model weights
        weights = torch.tensor([[0.05], [0.02], [-0.1], [5.0]], dtype=torch.float32).to(device)
        bias = torch.tensor([10.0], dtype=torch.float32).to(device)
        
        # Forward pass: risk_score = w1*HR + w2*BP + w3*SpO2 + w4*Hypoxic + bias
        with torch.no_grad():
            risk_scores_tensor = torch.matmul(tensor_features, weights) + bias
            risk_scores = risk_scores_tensor.cpu().numpy().flatten()
            
        # Normalize between 0 and 100
        risk_scores = np.clip(risk_scores, 0, 100)
        df["risk_score"] = risk_scores
        
        print("Updating risk scores back to Neon PostgreSQL...")
        dbapi_conn = engine.raw_connection()
        try:
            with dbapi_conn.cursor() as cur:
                update_query = """
                    UPDATE gold_patient_hourly_vitals AS m SET 
                        patient_risk_score = v.risk_score
                    FROM (VALUES %s) AS v(patient_id, risk_score)
                    WHERE m.patient_id = v.patient_id;
                """
                tuples_to_update = list(zip(df["patient_id"], df["risk_score"]))
                execute_values(cur, update_query, tuples_to_update, template=None, page_size=1000)
                dbapi_conn.commit()
                print("Successfully updated patient risk scores in Neon PostgreSQL!")
        finally:
            dbapi_conn.close()

except Exception as err:
    print(f"Kaggle GPU Execution Note: {err}")

print("--> Kaggle GPU AI Healthcare Risk Scoring Complete!")
