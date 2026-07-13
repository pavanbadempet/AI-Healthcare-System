# 🌀 AI Healthcare System — PySpark & Apache Airflow Data Platform

> A production-grade clinical MLOps & Big Data platform orchestrating ingestion pipelines, Medallion Lakehouse structures, schema evolution, slowly changing dimensions (SCD Type 2), and data lineage.

---

## 🚀 Overview

The data platform manages high-throughput ETL pipelines, patient health record consolidation, model retraining loops, and compliance-driven audit trails. Using **Apache Airflow** for orchestration and **Apache PySpark** for distributed compute, the system handles data processing at scale.

---

## 🏗️ Core Pipelines (DAGs)

The platform is organized into 3 production workflows located in [airflow/dags/](dags/):

### 1. Unified Healthcare Data Pipeline (`healthcare_data_pipeline`)
* **Purpose**: Primary ETL scheduler driving patient record updates, cleaning, and model retraining triggers.
* **Extraction**: Reads raw JSON clinical logs, telemetry measurements, and relational databases.
* **Transformation**: PySpark clean-up, missing value imputation, normalization, and feature tokenization.
* **Trigger Retraining**: Evaluates validation data drift and triggers Kaggle/Cloud retraining sessions when thresholds are exceeded.

### 2. Advanced Data Modeling & Time Travel (`healthcare_data_modeling`)
* **Purpose**: Implements slowly changing dimensions and historical state compliance.
* **SCD Type 2**: Automatically tracks patient demographics and clinical parameter updates over time using start/end timestamps and active/inactive flag versioning.
* **Schema Evolution**: Supports progressive database migrations, schema merges, and schema drift detection without pipeline downtime.
* **Time Travel Queries**: Demonstrates Delta Lake's historical recovery, allowing queries to be run against exact database states at specific timestamps.

### 3. High-Performance Delta Lake Operations (`delta_lake_operations`)
* **Purpose**: Optimization routines for low-latency analytics.
* **Liquid Clustering**: Replaces static partitioning with dynamic Z-Order clustering to speed up patient search.
* **CDC (Change Data Capture)**: Processes record insertions, updates, and deletions from transactional tables via Delta transaction logs.
* **Data Compaction**: Automates file compaction and metadata vacuuming to maintain high-performance disk access.

---

## 📊 Lineage & Compliance Tracking (`lineage_emitter.py`)

To satisfy strict healthcare compliance standards (HIPAA/GDPR), the system integrates an **OpenLineage** tracking client.
* **Metadata Captures**: Captures exact schema contracts, dataset origins, and pipeline task runs.
* **Lineage Audits**: Automatically logs lineage events (`START`, `COMPLETE`, `FAIL`) to `data/lineage/events/` as timestamped JSON documents, or forwards them to an external catalog collector (e.g. Marquez) if configured.

---

## 🛠️ Local Development & Setup

Ensure you have **Python 3.11** or **3.12** and **Java 11/17** (for PySpark) installed.

### 1. Install Orchestration Stack
```bash
pip install apache-airflow>=2.8.0 pyspark>=3.5.0 delta-spark>=3.1.0
```

### 2. Initialize Airflow Local Environment
```bash
cd airflow
$env:AIRFLOW_HOME = "."
airflow db init
```

### 3. Create Airflow Admin Account
```bash
airflow users create \
    --username admin \
    --firstname System \
    --lastname Administrator \
    --role Admin \
    --email admin@clinical.invalid \
    --password admin
```

### 4. Launch the Scheduler and Web UI
```bash
# Launches standalone Airflow server (Scheduler + Webserver)
airflow standalone
```
Open [http://127.0.0.1:8080](http://127.0.0.1:8080) in your browser and log in with your admin credentials.

---

## ⚙️ Environment Configuration

Set the following environment variables in your Airflow executor environment:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite:///./healthcare.db` | Primary transactional database source |
| `LAKEHOUSE_PATH` | `/tmp/healthcare_warehouse` | Path to storage directory for Delta Lake parquet files |
| `BACKEND_URL` | `http://127.0.0.1:8000` | Target FastAPI server for reloading retrained models |
| `OPENLINEAGE_URL` | — | (Optional) Remote OpenLineage collector URL (e.g., Marquez) |
| `DELTA_CATALOG` | `uc_healthcare_prod` | Unity Catalog database name target |
