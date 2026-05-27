# Airflow Model Retraining Pipeline

This directory contains the Airflow DAG for automated ML model retraining using **PySpark** for distributed data processing.

## Pipeline Overview

```
┌─────────────────┐    ┌────────────────────┐    ┌──────────────┐
│   Extract       │───►│   Transform        │───►│    Train     │
│ (PySpark JDBC)  │    │ (Spark DataFrame)  │    │  (Retrain)   │
└─────────────────┘    └────────────────────┘    └──────────────┘
                                                       │
                                                       ▼
┌─────────────┐    ┌────────────────┐    ┌──────────────┐
│   Notify    │◄───│    Deploy      │◄───│   Validate   │
│ (Complete)  │    │ (Reload API)   │    │  (Compare)   │
└─────────────┘    └────────────────┘    └──────────────┘
```

## Key Features (DE Best Practices)

| Feature | Why It Matters |
|---------|----------------|
| **PySpark JDBC** | Distributed DB reads with partitioning |
| **Spark SQL** | `get_json_object`, `when`, column transforms |
| **Parquet** | Columnar storage for analytics workloads |
| **Caching** | `df.cache()` for multi-pass operations |
| **Repartitioning** | Optimal parallelism for writes |
| **Adaptive Query** | `spark.sql.adaptive.enabled=true` |

## Schedule
- **Frequency**: Weekly (Every Sunday at 2 AM)
- **Catchup**: Disabled

## Tasks

| Task | Technology | Description |
|------|------------|-------------|
| `extract_data` | PySpark JDBC | Pull recent predictions from PostgreSQL |
| `transform_data` | Spark DataFrame | Parse JSON, feature engineering, partition |
| `train_models` | Python | Retrain models using existing scripts |
| `validate_models` | Python | Compare accuracy, decide deployment |
| `deploy_models` | REST API | Call `/admin/reload_models` endpoint |

## Local Development

### 1. Install Dependencies
```bash
pip install apache-airflow>=2.8.0 pyspark>=3.5.0
```

### 2. Download PostgreSQL JDBC Driver
```bash
# For production Spark cluster
wget https://jdbc.postgresql.org/download/postgresql-42.6.0.jar -P /opt/spark/jars/
```

### 3. Initialize Airflow
```bash
cd airflow
$env:AIRFLOW_HOME = "."
airflow db init
airflow standalone
```

### 4. Access UI
Open http://127.0.0.1:8080

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `BACKEND_URL` | API base URL (default: http://127.0.0.1:8000) |
| `ADMIN_JWT_TOKEN` | Pre-generated admin JWT for deployment |

## Production Deployment

For production, use managed services:
- **Databricks** (Spark + Airflow integration)
- **Google Cloud Composer** + Dataproc
- **AWS MWAA** + EMR
- **Azure Synapse** + Data Factory
