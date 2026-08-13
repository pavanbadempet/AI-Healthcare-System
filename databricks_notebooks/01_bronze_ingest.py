# Databricks notebook source
# MAGIC %md
# MAGIC # 01: Bronze Layer (Raw Telemetry Ingest)
# MAGIC Reads simulated JSON telemetry data and writes it to a Delta Lake Bronze table.
# MAGIC Supports both continuous real-time streaming and triggered batch processing.

# COMMAND ----------
dbutils.widgets.text("pipeline_mode", "batch")
pipeline_mode = dbutils.widgets.get("pipeline_mode")
print(f"Running Bronze Ingest in mode: {pipeline_mode}")

# COMMAND ----------
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType
from pyspark.sql.functions import col

# Define schema for the incoming stream
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
    StructField("timestamp", StringType(), True)
])

# COMMAND ----------
import os
spark.sql("CREATE VOLUME IF NOT EXISTS main.default.telemetry_volume")

os.makedirs("/Volumes/main.default/telemetry_volume/stream_in", exist_ok=True)
os.makedirs("/Volumes/main.default/telemetry_volume/stream_checkpoint", exist_ok=True)

streaming_df = (
    spark.readStream
    .schema(schema)
    .json("/Volumes/main.default/telemetry_volume/stream_in")
)

# Write to Bronze Delta Table
writer = (
    streaming_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/Volumes/main.default/telemetry_volume/stream_checkpoint/bronze")
    .table("main.default.bronze_patient_vitals")
)

if pipeline_mode == "streaming":
    # Run continuously 24/7 (Real-time)
    writer.trigger(processingTime="2 seconds").awaitTermination()
else:
    # Run once to process all queued data and shut down (Batch)
    writer.trigger(availableNow=True).awaitTermination()
