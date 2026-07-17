"""
Production-grade Medallion Architecture Pipeline
Ingests Bronze, cleanses to Silver, aggregates to Gold, optimizes table storage,
and prints compliance audit records using Delta Lake and Polars/delta-rs.
"""

import os
import shutil
import time
from datetime import datetime, timezone
import polars as pl
from deltalake import DeltaTable as RTDeltaTable
from deltalake.writer import write_deltalake

# Configurations
LAKEHOUSE_ROOT = os.path.join(os.getcwd(), "data", "lakehouse")
BRONZE_PATH = os.path.join(LAKEHOUSE_ROOT, "bronze", "patients")
SILVER_PATH = os.path.join(LAKEHOUSE_ROOT, "silver", "patients")
GOLD_PATH = os.path.join(LAKEHOUSE_ROOT, "gold", "patient_summary")

def run_medallion_pipeline():
    print("=" * 60)
    print("STARTING MEDALLION LAKEHOUSE ETL PIPELINE")
    print(f"Lakehouse Storage Directory: {LAKEHOUSE_ROOT}")
    print("=" * 60)

    # Clean existing directories for a fresh run
    if os.path.exists(LAKEHOUSE_ROOT):
        print("Cleaning up old lakehouse files...")
        shutil.rmtree(LAKEHOUSE_ROOT)
    os.makedirs(LAKEHOUSE_ROOT, exist_ok=True)

    # ---------------------------------------------------------
    # 1. BRONZE LAYER: Raw Data Ingestion
    # ---------------------------------------------------------
    print("\n[1/5] Ingesting Raw Data to Bronze Layer...")
    raw_data = [
        {"patient_id": "P101", "name": " JOHN DOE ", "email": "john@example.com", "dob": "1980-05-15", "gender": "Male", "created_at": "2026-07-16T12:00:00Z"},
        {"patient_id": "P102", "name": "jane smith", "email": "jane@example.co", "dob": "1992-11-22", "gender": "Female", "created_at": "2026-07-16T12:05:00Z"},
        {"patient_id": "P103", "name": "Bob Johnson", "email": "bob-invalid", "dob": "1975-02-09", "gender": "M", "created_at": "2026-07-16T12:10:00Z"},
        {"patient_id": "P101", "name": " JOHN DOE ", "email": "john@example.com", "dob": "1980-05-15", "gender": "Male", "created_at": "2026-07-16T12:15:00Z"}, # Duplicate
    ]
    df_raw = pl.DataFrame(raw_data)
    
    # Append ingestion metadata
    df_bronze = df_raw.with_columns([
        pl.lit(datetime.now(timezone.utc).isoformat()).alias("_ingestion_time"),
        pl.lit("source_api").alias("_source_system")
    ])
    
    write_deltalake(BRONZE_PATH, df_bronze, mode="overwrite")
    print(f"Bronze Table written successfully ({len(df_bronze)} records).")
    
    # ---------------------------------------------------------
    # 2. SILVER LAYER: Data Cleansing, Deduplication & Quality
    # ---------------------------------------------------------
    print("\n[2/5] Cleansing & Standardizing to Silver Layer...")
    
    # Read from Bronze using native Polars Delta integration
    df_silver_raw = pl.read_delta(BRONZE_PATH)
    
    # Transformations: Clean string spaces, standardize gender, parse DOB, deduplicate
    df_silver = df_silver_raw.with_columns([
        pl.col("name").str.strip_chars().str.to_titlecase(),
        pl.col("gender").replace({"M": "Male", "F": "Female"}),
        pl.col("dob").str.to_date("%Y-%m-%d", strict=False)
    ]).unique(subset=["patient_id"]) # Deduplicate on primary key
    
    # Assess Data Quality (Simulate backend PySpark checks in Polars)
    total_records = len(df_silver)
    non_null_emails = df_silver.filter(pl.col("email").is_not_null()).height
    completeness = non_null_emails / total_records if total_records > 0 else 1.0
    
    valid_emails = df_silver.filter(pl.col("email").str.contains(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")).height
    validity = valid_emails / total_records if total_records > 0 else 1.0
    
    print(f"Data Quality Check Results:")
    print(f"  - Completeness (non-null emails): {completeness:.2%}")
    print(f"  - Validity (valid email format): {validity:.2%}")
    
    write_deltalake(SILVER_PATH, df_silver, mode="overwrite", partition_by=["gender"])
    print(f"Silver Table written successfully ({len(df_silver)} cleansed, deduplicated records). Partitioned by: ['gender']")

    # ---------------------------------------------------------
    # 3. GOLD LAYER: Aggregated Business Metrics
    # ---------------------------------------------------------
    print("\n[3/5] Aggregating Metrics to Gold Layer...")
    
    # Read from Silver using native Polars Delta integration
    df_silver_loaded = pl.read_delta(SILVER_PATH)
    
    # Aggregate patient counts by gender
    df_gold = df_silver_loaded.group_by("gender").agg([
        pl.len().alias("patient_count"),
        pl.col("dob").mean().alias("avg_birth_date")
    ])
    
    write_deltalake(GOLD_PATH, df_gold, mode="overwrite")
    print(f"Gold Table written successfully. Demographics summary view:\n{df_gold.to_dicts()}")

    # ---------------------------------------------------------
    # 4. TIME TRAVEL: Querying Historical Table Snapshots
    # ---------------------------------------------------------
    print("\n[4/5] Executing Delta ACID Time Travel Verification...")
    
    # Update Bronze to simulate a new batch ingestion
    new_raw_data = [
        {"patient_id": "P104", "name": "Sarah Connor", "email": "sarah@skynet.com", "dob": "1965-11-10", "gender": "Female", "created_at": "2026-07-16T12:20:00Z"},
    ]
    df_new = pl.DataFrame(new_raw_data).with_columns([
        pl.lit(datetime.now(timezone.utc).isoformat()).alias("_ingestion_time"),
        pl.lit("source_api").alias("_source_system")
    ])
    
    # Append to Bronze (generates version 1)
    write_deltalake(BRONZE_PATH, df_new, mode="append")
    
    # Load Version 0 vs Version 1 using native Delta time travel
    df_v0 = pl.read_delta(BRONZE_PATH, version=0)
    df_v1 = pl.read_delta(BRONZE_PATH, version=1)
    
    print(f"Bronze Table Snapshot History:")
    print(f"  - Version 0 record count: {len(df_v0)}")
    print(f"  - Version 1 record count: {len(df_v1)}")

    # ---------------------------------------------------------
    # 5. STORAGE OPTIMIZATION & COMPLIANCE REPORTING
    # ---------------------------------------------------------
    print("\n[5/5] Executing Table Storage Optimization & Audit...")
    
    # Load Silver table metadata using delta-rs
    dt_silver = RTDeltaTable(SILVER_PATH)
    
    # Run Compaction & Vacuum
    dt_silver.optimize.compact()
    dt_silver.vacuum(retention_hours=168, dry_run=False, enforce_retention_duration=False)
    print("Storage optimized: Completed Compaction and Vacuum on Silver Table.")
    
    # Print transaction history details
    history = dt_silver.history()
    print("\n--- DELTA AUDIT COMPLIANCE REPORT (Silver Table) ---")
    for event in history[:3]:
        print(f"Version: {event.get('version')} | Action: {event.get('operation')} | Timestamp: {event.get('timestamp')}")
    print("----------------------------------------------------")
    
    print("\nMEDALLION ARCHITECTURE PIPELINE EXECUTED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_medallion_pipeline()
