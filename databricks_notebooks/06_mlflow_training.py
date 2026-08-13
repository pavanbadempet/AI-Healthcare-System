# Databricks notebook source
# MAGIC %md
# MAGIC # 06: MLflow Model Training & Unity Catalog Registry
# MAGIC This notebook demonstrates training a machine learning model using the pristine `silver_ml_training_data`,
# MAGIC logging metrics and hyperparameters via **MLflow**, and registering the final model directly into 
# MAGIC the **Unity Catalog Model Registry**.

# COMMAND ----------
# MAGIC %pip install mlflow scikit-learn pandas

# COMMAND ----------
import mlflow
import mlflow.sklearn
from pyspark.sql.functions import col
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import json

# Configure MLflow to use Unity Catalog
mlflow.set_registry_uri("databricks-uc")

print("Fetching Silver ML Training Data...")
# Read from the Silver training dataset
# We only want records that were explicitly marked as usable for training
df = spark.read.table("main.ai_healthcare.silver_ml_training_data")
pdf = df.toPandas()

if len(pdf) < 50:
    print("Not enough data to train a robust model. Please wait for more telemetry.")
    dbutils.notebook.exit("Not enough data")

print(f"Loaded {len(pdf)} training records.")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Data Preprocessing
# MAGIC The `features` column contains a JSON string of input features. We need to unpack this into separate columns.

# COMMAND ----------
# Parse JSON features into columns
features_df = pd.json_normalize(pdf['features'].apply(json.loads))
y = pdf['prediction_value']
X = features_df

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Model Training with MLflow Tracking

# COMMAND ----------
experiment_name = "/Shared/AI-Healthcare-Model-Retraining"
mlflow.set_experiment(experiment_name)

# Define hyperparameters
n_estimators = 100
max_depth = 10

with mlflow.start_run(run_name="RandomForest_Retraining_Run") as run:
    # 1. Log hyperparameters
    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("max_depth", max_depth)
    
    # 2. Train Model
    clf = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    clf.fit(X_train, y_train)
    
    # 3. Evaluate Model
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    
    # 4. Log Metrics
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("precision", precision)
    mlflow.log_metric("recall", recall)
    mlflow.log_metric("f1_score", f1)
    
    print(f"Model Training Complete. Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
    
    # 5. Log and Register the Model to Unity Catalog
    model_name = "main.ai_healthcare.disease_predictor"
    
    # Signature helps MLflow understand the expected input/output format
    signature = mlflow.models.signature.infer_signature(X_train, y_pred)
    
    mlflow.sklearn.log_model(
        sk_model=clf,
        artifact_path="model",
        signature=signature,
        registered_model_name=model_name
    )
    
    print(f"Model registered to Unity Catalog: {model_name}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Model Transition
# MAGIC In a real production environment, you would use Databricks Model Serving or Webhooks 
# MAGIC to automatically deploy this newly registered model into a REST API endpoint.
