# Databricks notebook source
# MAGIC %md
# MAGIC # AI Healthcare System - Medallion Architecture ETL
# MAGIC This notebook runs the Bronze, Silver, and Gold ETL pipelines using PySpark and Delta Lake.
# MAGIC It automatically syncs the processed Gold data and trained models back to a private Hugging Face Dataset.

# COMMAND ----------

# MAGIC %pip install huggingface_hub pandas numpy

# COMMAND ----------

import json
import logging
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd
from pyspark.sql.functions import col, lit, current_timestamp

# Ensure dbutils is available (it is natively available in Databricks, this is just for type hinting in IDEs)
try:
    dbutils = dbutils # type: ignore
except NameError:
    pass

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DatabricksETL")

# Databricks DBFS Target directories
BASE_DIR = "/dbfs/FileStore/healthcare_data"
BRONZE_DIR = os.path.join(BASE_DIR, "bronze")
SILVER_DIR = os.path.join(BASE_DIR, "silver")
GOLD_DIR = os.path.join(BASE_DIR, "gold")

# Ensure directories exist
for folder in [BRONZE_DIR, SILVER_DIR, GOLD_DIR]:
    os.makedirs(folder, exist_ok=True)

# COMMAND ----------

# Hugging Face Setup
# IMPORTANT: In Databricks, you should store your Hugging Face Token as a Databricks Secret.
# e.g. dbutils.secrets.get(scope="huggingface", key="hf_token")
try:
    HF_TOKEN = dbutils.secrets.get(scope="huggingface", key="hf_token")
    HF_DATASET_ID = dbutils.secrets.get(scope="huggingface", key="dataset_id")
except Exception:
    # Fallback to hardcoded or environment variables if secrets are not set up yet
    logger.warning("Databricks secrets not found. Using empty fallback.")
    HF_TOKEN = ""
    HF_DATASET_ID = ""

def get_hf_client():
    if not (HF_TOKEN and HF_DATASET_ID):
        logger.warning("Hugging Face credentials not provided. HF Sync disabled.")
        return None
    try:
        from huggingface_hub import HfApi
        return HfApi(token=HF_TOKEN)
    except Exception as e:
        logger.error(f"Failed to init Hugging Face Client: {e}")
        return None

def download_folder_from_hf(api, folder_name, local_dir):
    """Download a folder from the private HF Dataset."""
    if not api: return False
    logger.info(f"Downloading {folder_name}/ from Hugging Face private dataset {HF_DATASET_ID}...")
    try:
        files = api.list_repo_files(repo_id=HF_DATASET_ID, repo_type="dataset")
        matching_files = [f for f in files if f.startswith(f"{folder_name}/")]
        for file in matching_files:
            api.hf_hub_download(
                repo_id=HF_DATASET_ID,
                repo_type="dataset",
                filename=file,
                local_dir=local_dir,
                local_dir_use_symlinks=False
            )
        return True
    except Exception as e:
        logger.warning(f"No files found or download failed for {folder_name}/ : {e}")
        return False

def upload_file_to_hf(api, local_path, path_in_repo):
    """Upload a single file to a private HF Dataset."""
    if not api: return False
    try:
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=path_in_repo,
            repo_id=HF_DATASET_ID,
            repo_type="dataset"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to upload {path_in_repo} to HF: {e}")
        return False

# COMMAND ----------

hf_api = get_hf_client()

# --- PHASE 1: SYNC FROM CLOUD (Download Baseline Data) ---
download_folder_from_hf(hf_api, "bronze", BASE_DIR)
download_folder_from_hf(hf_api, "silver", BASE_DIR)

# COMMAND ----------
# MAGIC %md
# MAGIC ### BRONZE LAYER
# MAGIC *Extracting and storing raw data*

# COMMAND ----------

logger.info("=== STARTING BRONZE LAYER INGESTION ===")
# Note: In a production Databricks environment, you would use Databricks JDBC connectors to extract directly from your PostgreSQL instance.
# For Databricks Free Edition, we simulate the arrival of new raw data, or you can supply a JDBC connection string.

bronze_path = os.path.join(BRONZE_DIR, "raw_health_records.parquet")

# In this example, if the file doesn't exist, we'll create a dummy record to initialize the pipeline.
if not os.path.exists(bronze_path):
    dummy_data = pd.DataFrame([{
        "record_type": "diabetes",
        "data": '{"age": 45, "bmi": 28.5, "gender": "Male"}',
        "prediction": "high risk detected"
    }])
    dummy_data.to_parquet(bronze_path, index=False)
    logger.info("Created initial Bronze table.")

# Sync back to HF
upload_file_to_hf(hf_api, bronze_path, "bronze/raw_health_records.parquet")

# COMMAND ----------
# MAGIC %md
# MAGIC ### SILVER LAYER
# MAGIC *Cleaning, parsing JSON, and enforcing schema*

# COMMAND ----------

logger.info("=== STARTING SILVER LAYER TRANSFORMATION ===")
model_types = ['diabetes', 'heart', 'liver', 'kidney', 'lungs']

# Load bronze data
df_bronze = pd.read_parquet(bronze_path)

for mtype in model_types:
    silver_path = os.path.join(SILVER_DIR, f"{mtype}_cleaned.parquet")
    mtype_raw = df_bronze[df_bronze['record_type'] == mtype]
    
    parsed_records = []
    for _, r in mtype_raw.iterrows():
        try:
            data_dict = json.loads(r['data'])
            pred_str = str(r['prediction']).lower()
            
            # Simple rule-based target generation for analytics
            if 'detected' in pred_str or 'high' in pred_str:
                data_dict['target'] = 1
            else:
                data_dict['target'] = 0
            parsed_records.append(data_dict)
        except Exception:
            continue
            
    if parsed_records:
        df_silver = pd.DataFrame(parsed_records)
        df_silver.to_parquet(silver_path, index=False)
        logger.info(f"Silver conformed {mtype} dataset updated: {len(df_silver)} rows.")
        upload_file_to_hf(hf_api, silver_path, f"silver/{mtype}_cleaned.parquet")
    else:
        logger.info(f"No records found for {mtype}.")

# COMMAND ----------
# MAGIC %md
# MAGIC ### GOLD LAYER
# MAGIC *Aggregating insights for the business report*

# COMMAND ----------

logger.info("=== STARTING GOLD LAYER ANALYTICS ===")
start_time = time.time()

metrics = {
    "report_generated_at": datetime.now().isoformat(),
    "total_records_analyzed": 0,
    "prevalence_rates": {},
    "pipeline_execution": {
        "status": "success"
    }
}

total_rows = 0

for mtype in model_types:
    silver_path = os.path.join(SILVER_DIR, f"{mtype}_cleaned.parquet")
    if os.path.exists(silver_path):
        df = pd.read_parquet(silver_path)
        count = len(df)
        total_rows += count
        
        if "target" in df.columns:
            pos_rate = float((df["target"] == 1).mean())
            metrics["prevalence_rates"][mtype] = round(pos_rate * 100, 2)

metrics["total_records_analyzed"] = total_rows
metrics["pipeline_execution"]["duration_seconds"] = round(time.time() - start_time, 2)

# Write report
report_path = os.path.join(GOLD_DIR, "analyst_report.json")
with open(report_path, "w") as f:
    json.dump(metrics, f, indent=2)

logger.info(f"Gold Analyst JSON report generated.")
upload_file_to_hf(hf_api, report_path, "gold/analyst_report.json")

print("Medallion Pipeline Completed Successfully!")
