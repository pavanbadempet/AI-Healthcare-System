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
from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import FloatType, IntegerType, StringType, StructField, StructType

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

# Simulate generating random telemetry and appending to the raw Delta table
def generate_batch(batch_id):
    import random
    from datetime import datetime, timedelta

    import requests

    backend_url = os.getenv("BACKEND_URL", "https://pavanbadempet-ai-healthcare-system.hf.space")
    print(f"Attempting to fetch live telemetry from {backend_url}...")

    token = None
    try:
        # Authenticate with the HF Spaces backend
        auth_res = requests.post(f"{backend_url}/v1/token", data={"username": "admin", "password": "adminpass"}, timeout=15)
        if auth_res.status_code == 200:
            token = auth_res.json().get("access_token")
    except Exception as e:
        print(f"Auth fetch failed, falling back to local fallback data: {e}")

    data = []
    base_time = datetime.utcnow()

    if token:
        try:
            snap_res = requests.get(f"{backend_url}/v1/telemetry/snapshot", headers={"Authorization": f"Bearer {token}"}, timeout=15)
            if snap_res.status_code == 200:
                snapshot = snap_res.json()
                print(f"Successfully fetched live HF Spaces telemetry! Active Census: {snapshot.get('active_census')}")

                patient_counter = 1000
                # Generate a vital record for every REAL occupied bed returned by the endpoint
                for unit in snapshot.get("bed_units", []):
                    occupied = unit.get("occupied", 0)
                    unit_name = unit.get("unit", "Unknown")
                    dept_id = hash(unit_name) % 10

                    for _ in range(occupied):
                        patient_counter += 1
                        data.append((
                            patient_counter, 1, 9999, dept_id,
                            float(random.randint(60, 100)),
                            float(random.randint(110, 140)),
                            float(random.randint(70, 90)),
                            float(random.randint(95, 100)),
                            round(random.uniform(36.5, 37.5), 1),
                            float(random.randint(12, 18)),
                            f"live_{unit_name}_monitor",
                            (base_time - timedelta(seconds=random.randint(0, 10))).isoformat() + "Z"
                        ))
        except Exception as e:
            print(f"Failed to fetch snapshot: {e}")

    if not data:
        print("Using local mock generation as fallback...")
        num_records = random.randint(50, 200)
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
    print(f"Appended {len(data)} raw telemetry events to {raw_table_name}")

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

    writer.trigger(availableNow=True).toTable(silver_table_name)

    print(f"Streaming job initialized successfully. Streaming from {raw_table_name} to {silver_table_name}...")

    # ==========================================
    # NEW: INGEST CLICKSTREAM & PREDICTION LOGS
    # ==========================================
    def ingest_table_via_sql(table_name, target_bronze_raw, schema):
        import json

        import requests
        backend_url = os.getenv("BACKEND_URL", "https://pavanbadempet-ai-healthcare-system.hf.space")
        print(f"Pulling {table_name} from {backend_url}...")

        token = None
        try:
            auth_res = requests.post(f"{backend_url}/v1/token", data={"username": "admin", "password": "adminpass"}, timeout=15)
            if auth_res.status_code == 200:
                token = auth_res.json().get("access_token")
        except Exception as e:
            print(f"Auth failed: {e}")
            return

        if not token:
            print("No auth token, skipping SQL pull")
            return

        try:
            sql = f"SELECT * FROM {table_name} WHERE id > (SELECT COALESCE(MAX(id), 0) FROM {target_bronze_raw}) ORDER BY id ASC LIMIT 5000"
            # Using try/except around the subquery in case target_bronze_raw doesn't exist yet
            # we will just do a simple pull
            try:
                max_id_df = spark.sql(f"SELECT COALESCE(MAX(id), 0) as max_id FROM {target_bronze_raw}")
                max_id = max_id_df.collect()[0]["max_id"]
                sql = f"SELECT * FROM {table_name} WHERE id > {max_id} ORDER BY id ASC LIMIT 5000"
            except Exception:
                sql = f"SELECT * FROM {table_name} ORDER BY id ASC LIMIT 5000"

            res = requests.post(
                f"{backend_url}/api/v1/data-platform/sql/execute",
                json={"query": sql},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            if res.status_code == 200:
                rows = res.json().get("results", [])
                if rows:
                    import pandas as pd
                    pdf = pd.DataFrame(rows)
                    # For JSON columns, convert dicts back to string so spark doesn't complain about complex types
                    for col_name in pdf.columns:
                        if pdf[col_name].apply(lambda x: isinstance(x, (dict, list))).any():
                            pdf[col_name] = pdf[col_name].apply(json.dumps)

                    spark_df = spark.createDataFrame(pdf)
                    spark_df.write.format("delta").mode("append").saveAsTable(target_bronze_raw)
                    print(f"Appended {len(rows)} records to {target_bronze_raw}")
                else:
                    print(f"No new records for {table_name}")
            else:
                print(f"Failed to fetch {table_name}: {res.text}")
        except Exception as e:
            print(f"SQL pull failed: {e}")

    # Fetch clickstream events
    ingest_table_via_sql("clickstream_events", "bronze_clickstream_raw", None)

    # Fetch prediction feature attribution logs
    ingest_table_via_sql("feature_attribution_logs", "bronze_predictions_raw", None)
