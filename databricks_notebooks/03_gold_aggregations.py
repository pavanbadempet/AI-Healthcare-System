# Databricks notebook source
# MAGIC %md
# MAGIC # 03: Gold Layer (Aggregations)
# MAGIC Reads the cleaned Silver stream, aggregates patient vitals over 1-hour tumbling windows, 
# MAGIC handles late-arriving data via watermarking, and upserts to the Gold Medallion table.
# MAGIC Supports both continuous real-time streaming and triggered batch processing.

# COMMAND ----------
dbutils.widgets.text("pipeline_mode", "batch")
pipeline_mode = dbutils.widgets.get("pipeline_mode")
print(f"Running Gold Aggregations in mode: {pipeline_mode}")

# COMMAND ----------
from pyspark.sql.functions import col, avg, max, min, sum, when, window
from delta.tables import DeltaTable

# Initialize Gold table
spark.sql("""
CREATE TABLE IF NOT EXISTS apex.default.gold_patient_hourly_vitals (
    patient_id INT,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    avg_heart_rate FLOAT,
    max_systolic_bp FLOAT,
    min_spo2 FLOAT,
    hypoxic_events INT
) USING DELTA
""")

# COMMAND ----------
def process_gold_batch(microBatchDF, batchId):
    # Upsert (MERGE) aggregated windows into Gold table
    gold_table = DeltaTable.forName(spark, "apex.default.gold_patient_hourly_vitals")
    
    (gold_table.alias("target")
     .merge(
         microBatchDF.alias("source"),
         "target.patient_id = source.patient_id AND target.window_start = source.window_start"
     )
     .whenMatchedUpdateAll()
     .whenNotMatchedInsertAll()
     .execute())

# COMMAND ----------
# Read Silver as a Stream with Watermarking for late-arriving data (up to 2 hours late)
silver_stream = spark.readStream.table("apex.default.silver_patient_vitals")

gold_stream = (
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

# Write to Gold using foreachBatch in Update output mode (since we are using windowed aggregations)
writer = (gold_stream.writeStream
          .foreachBatch(process_gold_batch)
          .outputMode("update")
          .option("checkpointLocation", "/Volumes/apex/default/telemetry/stream_checkpoint/gold"))

if pipeline_mode == "streaming":
    writer.trigger(processingTime="1 minute").awaitTermination()
else:
    writer.trigger(availableNow=True).awaitTermination()
