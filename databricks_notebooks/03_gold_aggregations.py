# Databricks notebook source
# MAGIC %md
# MAGIC # 03: Gold Layer (Clinical Dashboard Aggregations)
# MAGIC Computes patient-level aggregates (hourly) for the AI Healthcare dashboard.

# COMMAND ----------
from pyspark.sql.functions import avg, min, max, sum, window, col
from delta.tables import DeltaTable

silver_df = spark.read.table("silver_patient_vitals")

# Compute Hourly Aggregates
gold_hourly_df = (
    silver_df
    .groupBy(
        col("patient_id"),
        window(col("timestamp"), "1 hour")
    )
    .agg(
        avg("heart_rate").alias("avg_heart_rate"),
        min("spo2").alias("min_spo2"),
        max("systolic_bp").alias("max_systolic_bp"),
        sum(col("is_hypertensive").cast("int")).alias("hypertensive_events"),
        sum(col("is_hypoxic").cast("int")).alias("hypoxic_events")
    )
)

# Overwrite Gold table (optimized for BI tools)
gold_hourly_df.write.format("delta").mode("overwrite").saveAsTable("gold_patient_hourly_vitals")

# Optimize table performance (Z-Ordering on patient_id and time)
spark.sql("OPTIMIZE gold_patient_hourly_vitals ZORDER BY (patient_id, window)")
