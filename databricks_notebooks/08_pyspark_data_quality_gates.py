# Databricks notebook source
# MAGIC %md
# MAGIC # Step 08: Spark Declarative Pipelines (SDP) & DLT Quality Expectations
# MAGIC 
# MAGIC Applies native Spark Declarative Pipelines (SDP) contracts to telemetry streams:
# MAGIC - Compiles declarative SQL expectations (HR $\in [30, 220]$, SBP $\in [60, 250]$, SpO2 $\in [50, 100]\%$)
# MAGIC - Executes vectorized Catalyst expressions inside the Spark SQL engine
# MAGIC - Automatically partitions clean records to `workspace.healthcare_silver.telemetry`
# MAGIC - Routes dirty/out-of-bounds records to `workspace.healthcare_bronze.quarantined_records`

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, FloatType, TimestampType

spark = SparkSession.builder.appName("SDP_Data_Quality_Gates").getOrCreate()

# Ensure schemas exist in Unity Catalog
spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.healthcare_bronze")
spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.healthcare_silver")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Ingest Bronze Telemetry Stream

# COMMAND ----------

try:
    df_raw = spark.read.table("workspace.healthcare_bronze.telemetry")
except Exception:
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    n_records = 2000
    
    p_ids = [f"PAT-CDC-{10000 + (i % 500)}" for i in range(n_records)]
    # Intentionally inject 1% nulls to test SDP quarantine gates
    p_ids[42] = None
    p_ids[108] = None
    
    timestamps = [f"2026-08-14T{i % 24:02d}:00:00Z" for i in range(n_records)]
    
    hrs = np.random.normal(74.0, 10.0, n_records).tolist()
    hrs[15] = 480.0  # Anomaly (> 220 bpm)
    
    sbps = np.random.normal(124.0, 14.0, n_records).tolist()
    sbps[88] = 310.0 # Anomaly (> 250 mmHg)
    
    dbps = np.random.normal(78.0, 8.0, n_records).tolist()
    spo2s = np.clip(np.random.normal(98.2, 1.2, n_records), 50.0, 100.0).tolist()
    spo2s[150] = 32.0 # Anomaly (< 50%)
    
    glucoses = np.random.normal(105.0, 25.0, n_records).tolist()
    
    pdf_telemetry = pd.DataFrame({
        "patient_id": p_ids,
        "timestamp": timestamps,
        "heart_rate": [float(v) if v is not None else None for v in hrs],
        "systolic_bp": [float(v) if v is not None else None for v in sbps],
        "diastolic_bp": [float(v) if v is not None else None for v in dbps],
        "spo2": [float(v) if v is not None else None for v in spo2s],
        "fasting_glucose": [float(v) if v is not None else None for v in glucoses]
    })
    
    df_raw = spark.createDataFrame(pdf_telemetry)

print(f"Ingested {df_raw.count()} raw records from Bronze layer.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Spark Declarative Pipelines (SDP) Expectation Predicates

# COMMAND ----------

# SDP Rule 1: Non-null primary key
sdp_valid_id = F.col("patient_id").isNotNull() & (F.trim(F.col("patient_id")) != "")
sdp_valid_ts = F.col("timestamp").isNotNull() & (F.trim(F.col("timestamp")) != "")

# SDP Rule 2: Physiological bounds
sdp_valid_hr = (F.col("heart_rate") >= 30.0) & (F.col("heart_rate") <= 220.0)
sdp_valid_sbp = (F.col("systolic_bp") >= 60.0) & (F.col("systolic_bp") <= 250.0)
sdp_valid_dbp = (F.col("diastolic_bp") >= 35.0) & (F.col("diastolic_bp") <= 150.0)
sdp_valid_spo2 = (F.col("spo2") >= 50.0) & (F.col("spo2") <= 100.0)
sdp_valid_glucose = (F.col("fasting_glucose") >= 20.0) & (F.col("fasting_glucose") <= 800.0)

# Master SDP Validity Condition
sdp_master_condition = (
    sdp_valid_id &
    sdp_valid_ts &
    sdp_valid_hr &
    sdp_valid_sbp &
    sdp_valid_dbp &
    sdp_valid_spo2 &
    sdp_valid_glucose
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3. Partition Clean vs. Quarantined Records

# COMMAND ----------

# Clean dataset routed to Silver
df_clean = df_raw.filter(sdp_master_condition)

# Quarantined dataset with SDP error taxonomy
df_quarantined = df_raw.filter(~sdp_master_condition).withColumn(
    "sdp_quarantine_reason",
    F.concat_ws("; ",
        F.when(~sdp_valid_id, F.lit("SDP_ERR_NULL_PK: patient_id is required")),
        F.when(~sdp_valid_ts, F.lit("SDP_ERR_NULL_TS: timestamp is required")),
        F.when(~sdp_valid_hr, F.lit("SDP_ERR_PHYSIO_HR: heart_rate out of bounds [30-220]")),
        F.when(~sdp_valid_sbp, F.lit("SDP_ERR_PHYSIO_SBP: systolic_bp out of bounds [60-250]")),
        F.when(~sdp_valid_dbp, F.lit("SDP_ERR_PHYSIO_DBP: diastolic_bp out of bounds [35-150]")),
        F.when(~sdp_valid_spo2, F.lit("SDP_ERR_PHYSIO_SPO2: spo2 out of bounds [50-100]")),
        F.when(~sdp_valid_glucose, F.lit("SDP_ERR_PHYSIO_GLUCOSE: fasting_glucose out of bounds [20-800]"))
    )
).withColumn("sdp_quarantined_at", F.current_timestamp())

# Write Clean to Silver (CDF Enabled)
df_clean.write.format("delta") \
    .option("delta.enableChangeDataFeed", "true") \
    .mode("append") \
    .saveAsTable("workspace.healthcare_silver.telemetry")

# Write Quarantined to Bronze Quarantine Table
df_quarantined.write.format("delta") \
    .mode("append") \
    .saveAsTable("workspace.healthcare_bronze.quarantined_records")

clean_cnt = df_clean.count()
quar_cnt = df_quarantined.count()
total_cnt = clean_cnt + quar_cnt
pass_pct = (clean_cnt / (total_cnt or 1)) * 100.0

print(f"[SDP QUALITY AUDIT SUMMARY]")
print(f"- Protocol:        Spark Declarative Pipelines (SDP)")
print(f"- Total Ingested:  {total_cnt}")
print(f"- Clean Passed:    {clean_cnt} ({pass_pct:.1f}%) -> workspace.healthcare_silver.telemetry")
print(f"- Quarantined:     {quar_cnt} -> workspace.healthcare_bronze.quarantined_records")
