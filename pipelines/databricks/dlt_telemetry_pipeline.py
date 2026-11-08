# Databricks notebook source
# MAGIC %md
# MAGIC # Delta Live Tables (DLT) Pipeline
# MAGIC Declarative, modern data engineering pipeline for Bronze -> Silver -> Gold Medallion Architecture.
# MAGIC This pipeline demonstrates Unity Catalog integration, Data Quality expectations, and automatic schema evolution.


import dlt
from pyspark.sql.functions import avg, col, current_timestamp, max, min, sum, when, window

# ==========================================
# 1. BRONZE LAYER (RAW INGESTION)
# ==========================================

@dlt.table(
    name="bronze_telemetry_raw",
    comment="Raw telemetry records directly from IoT devices or message queues",
    table_properties={"quality": "bronze"}
)
def bronze_telemetry_raw():
    # In a real DLT pipeline, this would use Auto Loader (cloudFiles)
    # spark.readStream.format("cloudFiles").option("cloudFiles.format", "json").load("/path/to/raw/data")

    # For this example, we assume there is an existing raw table or stream
    return (
        spark.readStream.format("delta")
        .table("main.ai_healthcare.bronze_telemetry_raw")
        .withColumn("_ingested_at", current_timestamp())
    )

@dlt.table(
    name="bronze_clickstream_raw",
    comment="Raw clickstream events ingested from the frontend",
    table_properties={"quality": "bronze"}
)
def bronze_clickstream_raw():
    return (
        spark.readStream.format("delta")
        .table("main.ai_healthcare.bronze_clickstream_raw")
    )


# ==========================================
# 2. SILVER LAYER (CLEANING & DATA QUALITY)
# ==========================================

# Use dlt expectations to define Data Quality rules.
# expect_or_drop drops rows that violate the condition.
# expect_or_fail halts the pipeline if a critical error occurs.
@dlt.table(
    name="silver_patient_vitals",
    comment="Cleaned and validated patient vitals",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_patient", "patient_id IS NOT NULL")
@dlt.expect_or_drop("valid_heart_rate", "heart_rate > 0 AND heart_rate < 300")
@dlt.expect_or_drop("valid_bp", "systolic_bp > 0 AND diastolic_bp > 0")
@dlt.expect_or_drop("valid_spo2", "spo2 >= 0 AND spo2 <= 100")
def silver_patient_vitals():
    df = dlt.read_stream("bronze_telemetry_raw")

    # Deduplicate within the micro-batch based on exact patient and timestamp
    clean_df = df.dropDuplicates(["patient_id", "timestamp"])

    # Convert timestamp if it's a string
    if dict(clean_df.dtypes).get("timestamp", "") == "string":
        clean_df = clean_df.withColumn("timestamp", col("timestamp").cast("timestamp"))

    return clean_df


@dlt.table(
    name="silver_clickstream",
    comment="Cleaned clickstream events",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_id", "id IS NOT NULL")
def silver_clickstream():
    df = dlt.read_stream("bronze_clickstream_raw")

    if dict(df.dtypes).get("created_at", "") == "string":
        df = df.withColumn("created_at", col("created_at").cast("timestamp"))

    return df

# ==========================================
# 3. GOLD LAYER (AGGREGATIONS & BUSINESS LOGIC)
# ==========================================

@dlt.table(
    name="gold_patient_hourly_vitals",
    comment="Hourly aggregated vitals for ML risk scoring",
    table_properties={"quality": "gold"}
)
def gold_patient_hourly_vitals():
    silver_stream = dlt.read_stream("silver_patient_vitals")

    return (
        silver_stream
        .withWatermark("timestamp", "2 hours")
        .groupBy(
            col("patient_id"),
            window(col("timestamp"), "1 hour")
        )
        .agg(
            avg("heart_rate").alias("avg_heart_rate"),
            max("systolic_bp").alias("max_systolic_bp"),
            min("spo2").alias("min_spo2"),
            sum(when(col("spo2") < 90, 1).otherwise(0)).alias("hypoxic_events")
        )
        .select(
            col("patient_id"),
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("avg_heart_rate"),
            col("max_systolic_bp"),
            col("min_spo2"),
            col("hypoxic_events")
        )
    )
