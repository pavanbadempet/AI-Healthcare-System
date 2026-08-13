# Databricks notebook source
# MAGIC %md
# MAGIC # 01: Bronze Layer (Raw Telemetry Ingest)
# MAGIC Reads simulated JSON telemetry data and writes it to a Delta Lake Bronze table.

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
dbutils.fs.mkdirs("/tmp/telemetry_stream_in")
dbutils.fs.mkdirs("/tmp/telemetry_stream_checkpoint")

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

# Wait for 10 seconds to process batch in job mode
bronze_query.awaitTermination(10)
