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
CREATE TABLE IF NOT EXISTS gold_patient_hourly_vitals (
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
    gold_table = DeltaTable.forName(spark, "gold_patient_hourly_vitals")
    
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
silver_stream = spark.readStream.table("silver_patient_vitals")

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
          .outputMode("update"))

if pipeline_mode == "streaming":
    try:
        writer.trigger(processingTime="1 minute").start().awaitTermination()
    except Exception:
        writer.trigger(availableNow=True).start().awaitTermination()
else:
    writer.trigger(availableNow=True).start().awaitTermination()

# COMMAND ----------
# MAGIC %md
# MAGIC ## Feature Engineering in Unity Catalog
# MAGIC Register the Gold Medallion table as a Feature Store table for machine learning consumption.
# MAGIC This provides lineage tracking and allows ML models to easily fetch the latest patient vitals at inference time.

# COMMAND ----------
if pipeline_mode == "batch":
    try:
        from databricks.feature_engineering import FeatureEngineeringClient
        
        fe = FeatureEngineeringClient()
        
        # Check if the feature table exists, if not create it
        table_name = "main.ai_healthcare.gold_patient_hourly_vitals"
        
        # We read the latest static version of the table to update the schema in Feature Store
        gold_df = spark.read.table("gold_patient_hourly_vitals")
        
        try:
            # Try to get the table to see if it exists
            fe.get_table(name=table_name)
            print(f"Feature table {table_name} already exists. It will be updated by the stream.")
        except Exception as e:
            # Create feature table using the Gold table as the source
            print(f"Creating Feature Table {table_name} in Unity Catalog...")
            fe.create_table(
                name=table_name,
                primary_keys=["patient_id", "window_start"],
                df=gold_df,
                schema_name="main.ai_healthcare",
                description="Aggregated hourly patient vitals including heart rate, BP, SpO2, and hypoxic events."
            )
            print("Feature table created successfully!")
    except ImportError:
        print("FeatureEngineeringClient not available in this environment. Skipping Feature Store registration.")
    except Exception as e:
        print(f"Skipping feature store registration: {e}")
