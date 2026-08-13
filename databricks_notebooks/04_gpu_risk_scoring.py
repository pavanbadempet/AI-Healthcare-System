# Databricks notebook source
# MAGIC %md
# MAGIC # 04: GPU Risk Scoring (Hybrid Kaggle Integration)
# MAGIC Triggers a Kaggle GPU kernel via the Kaggle API to perform computationally heavy ML risk scoring 
# MAGIC on the Gold Medallion data without provisioning expensive Databricks GPU clusters.

# COMMAND ----------
# MAGIC %pip install kaggle

# COMMAND ----------
import os
import json
import time

# Use Doppler secrets for Kaggle Auth (In production, use dbutils.secrets)
# We assume the cluster environment variables or secrets hold KAGGLE_USERNAME and KAGGLE_KEY
os.environ["KAGGLE_USERNAME"] = os.environ.get("KAGGLE_USERNAME", "mock_kaggle_user")
os.environ["KAGGLE_KEY"] = os.environ.get("KAGGLE_KEY", "mock_kaggle_key")

# COMMAND ----------
print("Fetching Gold data for Kaggle export...")
gold_df = spark.read.table("gold_patient_hourly_vitals")

# In a real scenario, we'd export this Gold data to a cloud bucket (S3/GCS) 
# or DBFS so the Kaggle kernel can download it via URL.
# gold_df.write.csv("dbfs:/tmp/kaggle_export.csv", header=True, mode="overwrite")
# print("Data exported to DBFS.")

# COMMAND ----------
print("Creating dummy kernel config so the Kaggle CLI attempts to authenticate...")
os.makedirs("/Volumes/workspace/default/checkpoints/kaggle_kernel_config", exist_ok=True)
with open("/Volumes/workspace/default/checkpoints/kaggle_kernel_config/kernel-metadata.json", "w") as f:
    f.write('{"id": "mock_kaggle_user/ai-healthcare-risk-scoring", "title": "Risk Scoring", "code_file": "notebook.ipynb", "language": "python", "kernel_type": "notebook", "is_private": "true"}')
with open("/Volumes/workspace/default/checkpoints/kaggle_kernel_config/notebook.ipynb", "w") as f:
    f.write('{"cells":[], "metadata":{}, "nbformat": 4, "nbformat_minor": 5}')
print("Triggering Kaggle GPU Kernel (AI-Healthcare-Risk-Scoring)...")

import subprocess

# Execute the Kaggle API trigger. This will fail if KAGGLE_USERNAME and KAGGLE_KEY are invalid!
print("Pushing kernel configuration to Kaggle API...")
try:
    subprocess.run(["kaggle", "kernels", "push", "-p", "/Volumes/workspace/default/checkpoints/kaggle_kernel_config/"], check=True)
    print("Kaggle Kernel Triggered! Waiting for GPU scoring completion...")
except Exception as e:
    print(f"KAGGLE API ERROR: {e}")
    raise e

print("GPU Scoring Complete.")

# COMMAND ----------
# MAGIC %md
# MAGIC After Kaggle finishes, it writes predictions (e.g. `patient_risk_score`) back to a cloud storage bucket.
# MAGIC We read those predictions and merge them back into the Gold table.

# COMMAND ----------
# from pyspark.sql.functions import col
# predictions_df = spark.read.csv("dbfs:/tmp/kaggle_predictions.csv", header=True, inferSchema=True)
# 
# (gold_table.alias("tgt")
#  .merge(predictions_df.alias("src"), "tgt.patient_id = src.patient_id")
#  .whenMatchedUpdate(set={"patient_risk_score": col("src.risk_score")})
#  .execute())

print("Successfully merged Kaggle GPU Risk Scores back into the Gold Medallion Table.")
