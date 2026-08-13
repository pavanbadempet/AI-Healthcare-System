# Databricks notebook source
# MAGIC %md
# MAGIC # 02: Silver Layer (Clinical Cleaning)
# MAGIC Cleans raw Bronze telemetry and writes to Silver.

# COMMAND ----------
from pyspark.sql.functions import col, to_timestamp, when
from delta.tables import DeltaTable

# Read Bronze
bronze_df = spark.read.table("bronze_patient_vitals")

# Clean & enrich
silver_df = (
    bronze_df
    .withColumn("timestamp", to_timestamp(col("timestamp")))
    .filter(col("heart_rate") > 0) # Drop invalid negative rates
    .withColumn("is_hypertensive", when(col("systolic_bp") >= 140, True).otherwise(False))
    .withColumn("is_hypoxic", when(col("spo2") <= 92, True).otherwise(False))
)

# Upsert into Silver using MERGE
if spark.catalog.tableExists("silver_patient_vitals"):
    silver_table = DeltaTable.forName(spark, "silver_patient_vitals")
    (silver_table.alias("tgt")
     .merge(silver_df.alias("src"), "tgt.patient_id = src.patient_id AND tgt.timestamp = src.timestamp")
     .whenNotMatchedInsertAll()
     .execute())
else:
    silver_df.write.format("delta").saveAsTable("silver_patient_vitals")
