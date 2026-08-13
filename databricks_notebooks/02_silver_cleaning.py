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
from pyspark.sql.functions import col
from delta.tables import DeltaTable

# Initialize the Silver table if it doesn't exist
spark.sql("""
CREATE TABLE IF NOT EXISTS apex.default.silver_patient_vitals (
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
    silver_table = DeltaTable.forName(spark, "apex.default.silver_patient_vitals")
    
    (silver_table.alias("target")
     .merge(
         clean_df.alias("source"),
         "target.patient_id = source.patient_id AND target.timestamp = source.timestamp"
     )
     .whenNotMatchedInsertAll()
     .execute())

# COMMAND ----------
# Read Bronze as a Stream
bronze_stream = spark.readStream.table("apex.default.bronze_patient_vitals")

# Write to Silver using foreachBatch
writer = (bronze_stream.writeStream
          .foreachBatch(process_silver_batch)
          .option("checkpointLocation", "/Volumes/apex/default/telemetry_volume/stream_checkpoint/silver"))

if pipeline_mode == "streaming":
    writer.trigger(processingTime="2 seconds").awaitTermination()
else:
    writer.trigger(availableNow=True).awaitTermination()
