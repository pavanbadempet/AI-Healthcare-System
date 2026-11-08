# Databricks notebook source
# MAGIC %md
# MAGIC # 02: Silver Layer (Cleaning & Enrichment)
# MAGIC Reads new records from the Bronze table via streaming, filters out bad data,
# MAGIC and performs an Upsert (MERGE) into the Silver table to prevent duplicates.
# MAGIC Supports both continuous real-time streaming and triggered batch processing.

# COMMAND ----------
dbutils.widgets.text("pipeline_mode", "batch")
pipeline_mode = dbutils.widgets.get("pipeline_mode")
print(f"Running Silver Cleaning in mode: {pipeline_mode}")

# COMMAND ----------
from delta.tables import DeltaTable
from pyspark.sql.functions import col

# Initialize the Silver table if it doesn't exist
spark.sql("""
CREATE TABLE IF NOT EXISTS silver_patient_vitals (
    patient_id INT,
    facility_id INT,
    encounter_id INT,
    department_id INT,
    heart_rate FLOAT,
    systolic_bp FLOAT,
    diastolic_bp FLOAT,
    spo2 FLOAT,
    temperature_c FLOAT,
    respiratory_rate FLOAT,
    source STRING,
    timestamp TIMESTAMP
) USING DELTA
""")

# COMMAND ----------
def process_silver_batch(microBatchDF, batchId):
    # 1. Clean data: Filter out nulls and invalid vitals
    clean_df = microBatchDF.filter(
        col("patient_id").isNotNull() &
        (col("heart_rate") > 0) &
        (col("heart_rate") < 300) &
        (col("systolic_bp") > 0) &
        (col("diastolic_bp") > 0) &
        (col("spo2") >= 0) &
        (col("spo2") <= 100)
    )

    # 2. Convert timestamp string to actual TimestampType
    clean_df = clean_df.withColumn("timestamp", col("timestamp").cast("timestamp"))

    # 3. Deduplicate based on exact patient and timestamp within the micro-batch
    clean_df = clean_df.dropDuplicates(["patient_id", "timestamp"])

    # 4. Upsert (MERGE) into Silver table using DeltaTable API
    silver_table = DeltaTable.forName(spark, "silver_patient_vitals")

    (silver_table.alias("target")
     .merge(
         clean_df.alias("source"),
         "target.patient_id = source.patient_id AND target.timestamp = source.timestamp"
     )
     .whenNotMatchedInsertAll()
     .execute())

# COMMAND ----------
# Read from Bronze
bronze_stream = spark.readStream.table("bronze_telemetry")

# Write to Silver using foreachBatch
checkpoint_path = "/Volumes/workspace/default/checkpoints/telemetry_silver"
writer = (bronze_stream.writeStream
          .foreachBatch(process_silver_batch)
          .option("checkpointLocation", checkpoint_path))

q1 = writer.trigger(availableNow=True).start()

# ==========================================
# NEW: PROCESS CLICKSTREAM & PREDICTIONS
# ==========================================

# 1. Init Silver Tables
spark.sql("""
CREATE TABLE IF NOT EXISTS silver_clickstream (
    id INT,
    user_id INT,
    session_id STRING,
    event_type STRING,
    event_data STRING,
    url STRING,
    created_at TIMESTAMP
) USING DELTA
""")

spark.sql("""
CREATE TABLE IF NOT EXISTS silver_ml_training_data (
    id INT,
    model_name STRING,
    model_version STRING,
    features STRING,
    attributions STRING,
    prediction_value INT,
    is_usable_for_training INT,
    created_at TIMESTAMP
) USING DELTA
""")

# 2. Clickstream Processing
def process_clickstream_batch(microBatchDF, batchId):

    clean_df = microBatchDF.filter(col("id").isNotNull())
    # Convert timestamps properly if needed
    if dict(clean_df.dtypes).get("created_at", "") == "string":
        clean_df = clean_df.withColumn("created_at", col("created_at").cast("timestamp"))

    # Upsert logic
    silver_table = DeltaTable.forName(spark, "silver_clickstream")
    (silver_table.alias("target")
     .merge(
         clean_df.alias("source"),
         "target.id = source.id"
     )
     .whenNotMatchedInsertAll()
     .execute())

# 3. ML Training Data Processing
def process_ml_training_batch(microBatchDF, batchId):

    # Filter for valid records AND ONLY where it's usable for training
    clean_df = microBatchDF.filter(
        col("id").isNotNull() &
        (col("is_usable_for_training") == 1)
    )

    if dict(clean_df.dtypes).get("created_at", "") == "string":
        clean_df = clean_df.withColumn("created_at", col("created_at").cast("timestamp"))

    silver_table = DeltaTable.forName(spark, "silver_ml_training_data")
    (silver_table.alias("target")
     .merge(
         clean_df.alias("source"),
         "target.id = source.id"
     )
     .whenNotMatchedInsertAll()
     .execute())

click_chk = "/Volumes/workspace/default/checkpoints/clickstream_silver"
ml_chk = "/Volumes/workspace/default/checkpoints/ml_training_silver"

try:
    q2 = (spark.readStream.format("delta").table("bronze_clickstream_raw")
          .writeStream.foreachBatch(process_clickstream_batch)
          .option("checkpointLocation", click_chk))
    q2 = q2.trigger(availableNow=True).start()
except Exception as e:
    print(f"Skipping clickstream stream: {e}")
    q2 = None

try:
    q3 = (spark.readStream.format("delta").table("bronze_predictions_raw")
          .writeStream.foreachBatch(process_ml_training_batch)
          .option("checkpointLocation", ml_chk))
    q3 = q3.trigger(availableNow=True).start()
except Exception as e:
    print(f"Skipping ML training stream: {e}")
    q3 = None

q1.awaitTermination()
if q2: q2.awaitTermination()
if q3: q3.awaitTermination()
