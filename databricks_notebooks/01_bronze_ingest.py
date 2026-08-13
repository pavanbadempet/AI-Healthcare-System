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
from pyspark.sql.functions import col, current_timestamp

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

import os

# Instead of using cloudFiles and Unity Catalog Volumes (which have Serverless permission constraints),
# we will simulate raw ingestion by writing to a raw Delta table, then streaming from it.

raw_table_name = "bronze_telemetry_raw"
silver_table_name = "bronze_telemetry"
checkpoint_path = "/Volumes/workspace/default/checkpoints/telemetry_bronze"

import os
os.makedirs(checkpoint_path, exist_ok=True)

# Simulate generating random telemetry and appending to the raw Delta table
def generate_batch(batch_id):
    import random
    from datetime import datetime, timedelta
    
    num_records = random.randint(50, 200)
    data = []
    base_time = datetime.utcnow()
    
    for i in range(num_records):
        patient_id = random.randint(1, 1000)
        facility_id = random.randint(1, 5)
        encounter_id = random.randint(10000, 99999)
        department_id = random.randint(1, 10)
        
        heart_rate = float(random.randint(60, 120))
        systolic_bp = float(random.randint(110, 150))
        diastolic_bp = float(random.randint(70, 95))
        spo2 = float(random.randint(92, 100))
        temperature_c = round(random.uniform(36.5, 38.5), 1)
        respiratory_rate = float(random.randint(12, 20))
        
        source = "device_" + str(random.randint(100, 200))
        timestamp = (base_time - timedelta(seconds=random.randint(0, 60))).isoformat() + "Z"
        
        data.append((
            patient_id, facility_id, encounter_id, department_id,
            heart_rate, systolic_bp, diastolic_bp, spo2,
            temperature_c, respiratory_rate, source, timestamp
        ))
        
    df = spark.createDataFrame(data, schema)
    # Write to raw ledger table
    df.write.format("delta").mode("append").saveAsTable(raw_table_name)
    print(f"Appended {num_records} raw telemetry events to {raw_table_name}")

if pipeline_mode == "batch":
    # In batch mode, we generate one chunk of raw data to be processed by the stream
    generate_batch(1)

print(f"Starting Delta Stream from {raw_table_name}...")

# 1. Read Stream using Delta table as source
try:
    streaming_df = (
        spark.readStream
        .format("delta")
        .table(raw_table_name)
        .withColumn("_ingested_at", current_timestamp())
    )
except Exception as e:
    print(f"Raw table might not exist yet if this is the very first run: {e}")
    generate_batch(0)
    streaming_df = (
        spark.readStream
        .format("delta")
        .table(raw_table_name)
        .withColumn("_ingested_at", current_timestamp())
    )

# 2. Write Stream to Bronze Delta Lake Managed Table
writer = (streaming_df.writeStream
          .format("delta")
          .outputMode("append")
          .option("checkpointLocation", checkpoint_path))

if pipeline_mode == "streaming":
    # For continuous execution
    writer.trigger(processingTime="5 seconds").toTable(silver_table_name)
else:
    # Databricks Workflows (Serverless jobs) typically use availableNow for micro-batch
    writer.trigger(availableNow=True).toTable(silver_table_name)

print(f"Streaming job initialized successfully. Streaming from {raw_table_name} to {silver_table_name}...")
