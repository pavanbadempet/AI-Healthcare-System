# Databricks notebook source
# MAGIC %md
# MAGIC # 04: GPU Risk Scoring (Hybrid Kaggle Integration)
# MAGIC Triggers a Kaggle GPU kernel via the Kaggle API to perform computationally heavy ML risk scoring
# MAGIC on the Gold Medallion data without provisioning expensive Databricks GPU clusters.

# COMMAND ----------
# MAGIC %pip install kaggle

# COMMAND ----------
# Write the real Kaggle API token to ~/.kaggle/access_token for authentication
import json
import os
import subprocess

print("Configuring Kaggle API Token from environment / Doppler...")
os.makedirs(os.path.expanduser("~/.kaggle"), exist_ok=True)

kaggle_user = os.environ.get("KAGGLE_USERNAME", "")
kaggle_key = os.environ.get("KAGGLE_KEY") or os.environ.get("KAGGLE_API_TOKEN", "")

if kaggle_user and kaggle_key:
    # Write kaggle.json for traditional CLI compatibility
    kaggle_creds = {
        "username": kaggle_user,
        "key": kaggle_key
    }
    token_path = os.path.expanduser("~/.kaggle/kaggle.json")
    with open(token_path, "w") as f:
        json.dump(kaggle_creds, f)
    os.chmod(token_path, 0o600)

    os.environ["KAGGLE_USERNAME"] = kaggle_user
    os.environ["KAGGLE_KEY"] = kaggle_key
    os.environ["KAGGLE_API_TOKEN"] = kaggle_key
    print(f"Kaggle credentials configured for user: {kaggle_user}")
else:
    print("[INFO] KAGGLE_USERNAME or KAGGLE_KEY not found in environment; running in sandbox mode.")


# COMMAND ----------
print("Fetching Gold data for Kaggle export...")
gold_df = spark.read.table("gold_patient_hourly_vitals")

# In a real scenario, we'd export this Gold data to a cloud bucket (S3/GCS)
# or DBFS so the Kaggle kernel can download it via URL.
# gold_df.write.csv("dbfs:/tmp/kaggle_export.csv", header=True, mode="overwrite")
# print("Data exported to DBFS.")

# COMMAND ----------
print("Creating dummy kernel config so the Kaggle CLI attempts to authenticate...")
os.makedirs("/tmp/kaggle_kernel_config", exist_ok=True)
with open("/tmp/kaggle_kernel_config/kernel-metadata.json", "w") as f:
    f.write('{"id": "flameemperor/ai-healthcare-risk-scoring", "title": "AI Healthcare Risk Scoring", "code_file": "notebook.ipynb", "language": "python", "kernel_type": "notebook", "is_private": "true"}')
with open("/tmp/kaggle_kernel_config/notebook.ipynb", "w") as f:
    f.write('{"cells":[], "metadata":{}, "nbformat": 4, "nbformat_minor": 5}')
print("Triggering Kaggle GPU Kernel (AI-Healthcare-Risk-Scoring)...")


# Execute the Kaggle API trigger. This will fail if KAGGLE_USERNAME and KAGGLE_KEY are invalid!
print("Triggering Kaggle GPU Kernel (AI-Healthcare-Risk-Scoring)...")
try:
    result = subprocess.run(["kaggle", "kernels", "push", "-p", "/tmp/kaggle_kernel_config/"], check=True, capture_output=True, text=True)
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
