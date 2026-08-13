import os
import requests
import base64
import json
import time

DATABRICKS_INSTANCE = "https://dbc-3f46f628-dd14.cloud.databricks.com"
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
}

NOTEBOOK_CONTENT = """
# Databricks notebook source
# MAGIC %md
# MAGIC # AI Healthcare System: Vitals Streaming Pipeline (Delta Lake)
# MAGIC This pipeline reads simulated telemetry data and writes it to a Delta Lake Bronze table.

# COMMAND ----------
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType, TimestampType
from pyspark.sql.functions import col, from_json

# Define schema for the incoming Kafka/JSON stream
schema = StructType([
    StructField("patient_id", IntegerType(), True),
    StructField("facility_id", IntegerType(), True),
    StructField("encounter_id", IntegerType(), True),
    StructField("department_id", IntegerType(), True),
    StructField("heart_rate", FloatType(), True),
    StructField("systolic_bp", FloatType(), True),
    StructField("diastolic_bp", FloatType(), True),
    StructField("spo2", FloatType(), True),
    StructField("temperature_c", FloatType(), True),
    StructField("respiratory_rate", FloatType(), True),
    StructField("source", StringType(), True),
    StructField("timestamp", StringType(), True) # Parse to timestamp later
])

# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Bronze Layer (Raw Telemetry)

# COMMAND ----------
dbutils.fs.mkdirs("/tmp/telemetry_stream_in")
dbutils.fs.mkdirs("/tmp/telemetry_stream_checkpoint")

# In Community Edition, we read from a DBFS directory (which we can populate with API or simulate_vitals_stream.py)
streaming_df = (
    spark.readStream
    .schema(schema)
    .json("dbfs:/tmp/telemetry_stream_in")
)

# Write to Bronze Delta Table
bronze_query = (
    streaming_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "dbfs:/tmp/telemetry_stream_checkpoint")
    .table("bronze_patient_vitals")
)
"""

def upload_notebook():
    # First, get the current user's email
    me_url = f"{DATABRICKS_INSTANCE}/api/2.0/preview/scim/v2/Me"
    me_response = requests.get(me_url, headers=HEADERS)
    
    if me_response.status_code != 200:
        print(f"[ERROR] Failed to fetch current user info: {me_response.status_code}")
        print(me_response.text)
        return
        
    user_email = me_response.json().get("userName")
    print(f"Deploying to user workspace: {user_email}")
    
    url = f"{DATABRICKS_INSTANCE}/api/2.0/workspace/import"
    
    # Base64 encode the notebook content
    content_b64 = base64.b64encode(NOTEBOOK_CONTENT.encode("utf-8")).decode("utf-8")
    
    payload = {
        "path": f"/Workspace/Users/{user_email}/AI_Healthcare_Pipeline",
        "format": "SOURCE",
        "language": "PYTHON",
        "content": content_b64,
        "overwrite": True
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        if response.status_code == 200:
            print("[SUCCESS] Successfully deployed PySpark Pipeline notebook to Databricks Free Edition!")
        else:
            print(f"[ERROR] Failed to deploy notebook: {response.status_code}")
            print(response.text)
    except requests.exceptions.SSLError as e:
        print("[ERROR] Network SSL Error: The connection to Databricks Community Edition was blocked or dropped.")
        print("Please run this script from your local machine to bypass the sandbox network restrictions.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    print("Deploying AI Healthcare Pipeline to Databricks...")
    upload_notebook()
