# Databricks Free Edition Integration & Medallion Lakehouse

This guide explains how to run the Medallion Architecture ETL & Real-Time Streaming pipelines for the AI-Healthcare-System using **Databricks Free Edition** with **Unity Catalog**.

By running the lakehouse pipeline in Databricks Free Edition, you leverage full enterprise-grade cloud data engineering capabilities (Unity Catalog 3-level namespaces, Structured Streaming, Delta Lake Change Data Feed, and Managed Volumes) without incurring any cloud costs.

---

## 🏛️ Architecture Overview

Databricks Free Edition provides full access to:
1. **Unity Catalog**: 3-level governed namespaces (`workspace.<schema>.<table>`) across `healthcare_bronze`, `healthcare_silver`, `healthcare_gold`, `healthcare_governance`, and `healthcare_mlops`.
2. **Databricks Workflows**: Multi-task automated DAGs for batch ingestion and real-time streaming pipelines.
3. **Managed Volumes**: Unified storage for DICOM imaging, FHIR bundles, and ONNX model weights (`/Volumes/workspace/default/checkpoints/`).
4. **Delta Lake Medallion**: Automated data quality checks, schema evolution, and Change Data Feed (CDF).

---

## 🚀 Step 1: Workspace & Git Integration

1. Log into your **Databricks Free Edition** workspace.
2. In the sidebar, navigate to **Workspace** -> **Repos / Git Providers**.
3. Link your GitHub repository: `https://github.com/pavanbadempet/AI-Healthcare-System.git`.
4. All pipeline notebooks located in `databricks_notebooks/` will be instantly available.

---

## ⚙️ Step 2: Configure Workspace Secrets & Token

1. Generate a **Personal Access Token (PAT)** in Databricks: **User Settings** -> **Developer** -> **Access Tokens**.
2. Inject your token into Doppler or environment variables:
   ```bash
   doppler secrets set DATABRICKS_TOKEN="dapi..."
   ```

---

## 🔄 Step 3: Run Automated Workflows & Streaming Pipelines

You can trigger and audit the complete medallion pipeline directly via the automated CLI scripts:

```bash
# Execute Batch Medallion Pipeline (Bronze -> Silver -> Gold -> Neon)
doppler run -- python scripts/run_databricks_medallion_pipeline.py

# Deploy & Update Real-Time Structured Streaming Job
doppler run -- python scripts/create_databricks_streaming_job.py
```

### Automated Multi-Task Pipeline Execution Flow:
1. `step_00_unity_catalog_governance_setup`: Initializes schemas, HIPAA audit tables, and masking functions.
2. `step_01_bronze_ingest`: Ingests telemetry, clickstream, and clinical events.
3. `step_02_silver_cleaning`: Cleanses, standardizes, and validates physiological ranges.
4. `step_03_gold_aggregations`: Generates longitudinal patient risk profiles and cohort aggregates.
5. `step_04_gpu_risk_scoring`: GPU risk scoring and MLflow inference.
6. `step_05_export_to_neon`: Secure export to Neon Postgres with immutable HIPAA audit logging.
