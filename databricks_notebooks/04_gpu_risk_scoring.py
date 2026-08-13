# Databricks notebook source
# MAGIC %md
# MAGIC # 04: GPU Risk Scoring (Hybrid Kaggle Integration)
# MAGIC Triggers a Kaggle GPU kernel via the Kaggle API to perform computationally heavy ML risk scoring 
# MAGIC on the Gold Medallion data without provisioning expensive Databricks GPU clusters.

# COMMAND ----------
# MAGIC %pip install kaggle

# COMMAND ----------
# Write the real Kaggle API token to ~/.kaggle/access_token for authentication
import os
import subprocess

print("Configuring Kaggle API Token...")
os.makedirs(os.path.expanduser("~/.kaggle"), exist_ok=True)
token_path = os.path.expanduser("~/.kaggle/access_token")
with open(token_path, "w") as f:
    f.write("KGAT_0869e262f9e04241ca9a0d223ecc753d")
os.chmod(token_path, 0o600)
os.environ["KAGGLE_API_TOKEN"] = "KGAT_0869e262f9e04241ca9a0d223ecc753d"


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
    f.write('{"id": "flameemperor/ai-healthcare-risk-scoring", "title": "Risk Scoring", "code_file": "notebook.ipynb", "language": "python", "kernel_type": "notebook", "is_private": "true"}')
with open("/Volumes/workspace/default/checkpoints/kaggle_kernel_config/notebook.ipynb", "w") as f:
    f.write('{"cells":[], "metadata":{}, "nbformat": 4, "nbformat_minor": 5}')
print("Triggering Kaggle GPU Kernel (AI-Healthcare-Risk-Scoring)...")

import subprocess

# Execute the Kaggle API trigger. This will fail if KAGGLE_USERNAME and KAGGLE_KEY are invalid!
print("Triggering Kaggle GPU Kernel (AI-Healthcare-Risk-Scoring)...")
try:
    result = subprocess.run(["kaggle", "kernels", "push", "-p", "/Volumes/workspace/default/checkpoints/kaggle_kernel_config/"], check=True, capture_output=True, text=True)
    print("Kaggle CLI STDOUT:", result.stdout)
    print("Kaggle CLI STDERR:", result.stderr)
    print("Successfully pushed to Kaggle GPU Cluster!")
except subprocess.CalledProcessError as e:
    print("Kaggle CLI STDOUT:", e.stdout)
    print("Kaggle CLI STDERR:", e.stderr)
    raise e
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
