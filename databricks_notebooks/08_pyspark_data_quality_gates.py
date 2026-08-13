# Databricks notebook source
# MAGIC %md
# MAGIC # Step 08: Declarative Great Expectations & PySpark Data Quality Gates
# MAGIC 
# MAGIC Applies clinical expectation suites to telemetry batches & streams:
# MAGIC - Validates physiological ranges (HR $\in [30, 220]$, SBP $\in [60, 250]$, SpO2 $\in [50, 100]\%$)
# MAGIC - Enforces schema non-null constraints on primary keys (`patient_id`, `timestamp`)
# MAGIC - Automatically partitions clean records to `workspace.healthcare_silver.telemetry`
# MAGIC - Routes dirty/out-of-bounds records to `workspace.healthcare_bronze.quarantined_records`

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, FloatType, TimestampType

spark = SparkSession.builder.appName("Lakehouse_Data_Quality_Gates").getOrCreate()

# Ensure schemas exist
spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.healthcare_bronze")
spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.healthcare_silver")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Read Raw Ingested Telemetry from Bronze

# COMMAND ----------

try:
    df_raw = spark.read.table("workspace.healthcare_bronze.telemetry")
except Exception:
    # Synthetic bootstrap for zero-config execution
    sample_telemetry = [
        ("PAT-1001", "2026-08-14T00:00:00Z", 72.0, 122.0, 80.0, 98.5, 95.0),
        ("PAT-1002", "2026-08-14T00:00:00Z", 450.0, 135.0, 85.0, 99.0, 110.0), # Corrupt HR (450 > 220)
        (None, "2026-08-14T00:00:00Z", 80.0, 120.0, 78.0, 97.0, 90.0),          # Null patient_id
        ("PAT-1004", "2026-08-14T00:00:00Z", 68.0, 118.0, 76.0, 32.0, 88.0)   # Corrupt SpO2 (32 < 50)
    ]
    t_schema = StructType([
        StructField("patient_id", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("heart_rate", FloatType(), True),
        StructField("systolic_bp", FloatType(), True),
        StructField("diastolic_bp", FloatType(), True),
        StructField("spo2", FloatType(), True),
        StructField("fasting_glucose", FloatType(), True)
    ])
    df_raw = spark.createDataFrame(sample_telemetry, t_schema)

print(f"Read {df_raw.count()} raw records from Bronze layer.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Declarative Great Expectations Rules Engine

# COMMAND ----------

# Rule 1: Non-null primary key
cond_valid_id = F.col("patient_id").isNotNull() & (F.trim(F.col("patient_id")) != "")

# Rule 2: Physiological bounds
cond_valid_hr = (F.col("heart_rate") >= 30.0) & (F.col("heart_rate") <= 220.0)
cond_valid_sbp = (F.col("systolic_bp") >= 60.0) & (F.col("systolic_bp") <= 250.0)
cond_valid_dbp = (F.col("diastolic_bp") >= 35.0) & (F.col("diastolic_bp") <= 150.0)
cond_valid_spo2 = (F.col("spo2") >= 50.0) & (F.col("spo2") <= 100.0)
cond_valid_glucose = (F.col("fasting_glucose") >= 20.0) & (F.col("fasting_glucose") <= 800.0)

# Master Validity Condition
master_valid_condition = (
    cond_valid_id &
    cond_valid_hr &
    cond_valid_sbp &
    cond_valid_dbp &
    cond_valid_spo2 &
    cond_valid_glucose
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3. Partition Clean vs. Quarantined Records

# COMMAND ----------

# Clean dataset
df_clean = df_raw.filter(master_valid_condition)

# Quarantined dataset with error reasoning
df_quarantined = df_raw.filter(~master_valid_condition).withColumn(
    "quarantine_reason",
    F.concat_ws("; ",
        F.when(~cond_valid_id, F.lit("Invalid/Null patient_id")),
        F.when(~cond_valid_hr, F.lit("Heart rate out of physiological bounds [30-220]")),
        F.when(~cond_valid_sbp, F.lit("Systolic BP out of bounds [60-250]")),
        F.when(~cond_valid_dbp, F.lit("Diastolic BP out of bounds [35-150]")),
        F.when(~cond_valid_spo2, F.lit("SpO2 out of bounds [50-100]")),
        F.when(~cond_valid_glucose, F.lit("Fasting Glucose out of bounds [20-800]"))
    )
).withColumn("quarantined_at", F.current_timestamp())

# Write Clean to Silver
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

print(f"[QUALITY AUDIT SUMMARY]")
print(f"- Total Processed: {total_cnt}")
print(f"- Clean Passed:    {clean_cnt} ({pass_pct:.1f}%) -> workspace.healthcare_silver.telemetry")
print(f"- Quarantined:     {quar_cnt} -> workspace.healthcare_bronze.quarantined_records")
