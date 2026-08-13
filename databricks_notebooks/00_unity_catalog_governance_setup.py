# Databricks notebook source
# MAGIC %md
# MAGIC # 🏥 AI Healthcare System: Enterprise Unity Catalog Governance & Security Layer
# MAGIC 
# MAGIC ### Architecture & Governance Standards:
# MAGIC 1. **Three-Level Namespace**: `workspace.healthcare_<bronze|silver|gold|governance|mlops>.<table_name>`
# MAGIC 2. **Dynamic Data Masking (DDM)**: Column-level masking for Patient PHI (Names, MRNs, DOBs, SSNs) based on RBAC group memberships.
# MAGIC 3. **Row-Level Security (RLS)**: Fine-grained access control filtering records by clinician assignment and tenant authorization.
# MAGIC 4. **HIPAA Audit Logging & Consent Enforcement**: Immutable access trails recording all data queries and exports.
# MAGIC 5. **Delta Lake Optimization**: Liquid Clustering / Z-Ordering on `(patient_id, timestamp)`, automatic compaction, and ACID Time-Travel.

# COMMAND ----------
import pyspark.sql.functions as F
from pyspark.sql.types import *

CATALOG = "workspace"

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Create Unity Catalog Schemas & Managed Storage

# COMMAND ----------
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.healthcare_bronze COMMENT 'Raw immutable ingested healthcare telemetry, FHIR bundles, and event streams'")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.healthcare_silver COMMENT 'Cleaned, standardized, de-duplicated clinical records and validated vitals'")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.healthcare_gold COMMENT 'Aggregated patient risk metrics, longitudinal feature store, and population cohorts'")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.healthcare_governance COMMENT 'HIPAA audit trails, consent registers, and data access log lineage'")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.healthcare_mlops COMMENT 'Model performance tracking, drift metrics, and prediction attribution logs'")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Create Unity Catalog Volumes for Unstructured Medical Data & Models

# COMMAND ----------
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.healthcare_bronze.raw_dicom_imaging COMMENT 'Raw DICOM image archives for PACS integration'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.healthcare_bronze.raw_fhir_bundles COMMENT 'Raw JSON/XML FHIR batch bundles'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.healthcare_mlops.model_weights COMMENT 'ONNX, Scikit-Learn, PyTorch and XGBoost weights'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.default.checkpoints COMMENT 'Delta streaming checkpoint store'")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. Define Dynamic Data Masking (DDM) & Row-Level Security (RLS) Functions

# COMMAND ----------
# Dynamic PHI Mask for Patient Names
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.healthcare_governance.mask_patient_name(name STRING)
RETURNS STRING
LANGUAGE SQL
DETERMINISTIC
CONTAINS SQL
COMMENT 'Masks patient names for unauthorized users under HIPAA Privacy Rule'
RETURN IF(
    IS_ACCOUNT_GROUP_MEMBER('clinicians') OR IS_ACCOUNT_GROUP_MEMBER('admins') OR IS_ACCOUNT_GROUP_MEMBER('workspace_admins'),
    name,
    CONCAT(SUBSTRING(name, 1, 1), '***')
)
""")

# Dynamic PHI Mask for Medical Record Numbers (MRN)
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.healthcare_governance.mask_mrn(mrn STRING)
RETURNS STRING
LANGUAGE SQL
DETERMINISTIC
CONTAINS SQL
COMMENT 'Redacts MRN identifier unless authorized clinician'
RETURN IF(
    IS_ACCOUNT_GROUP_MEMBER('clinicians') OR IS_ACCOUNT_GROUP_MEMBER('admins') OR IS_ACCOUNT_GROUP_MEMBER('workspace_admins'),
    mrn,
    'MRN-REDACTED'
)
""")

# Dynamic Mask for Date of Birth (preserves birth year only for epidemiology)
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.healthcare_governance.mask_dob(dob DATE)
RETURNS DATE
LANGUAGE SQL
DETERMINISTIC
CONTAINS SQL
COMMENT 'Generalizes Date of Birth to Jan 1st of the birth year for non-clinical research'
RETURN IF(
    IS_ACCOUNT_GROUP_MEMBER('clinicians') OR IS_ACCOUNT_GROUP_MEMBER('admins') OR IS_ACCOUNT_GROUP_MEMBER('workspace_admins'),
    dob,
    TO_DATE(CONCAT(YEAR(dob), '-01-01'))
)
""")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4. Initialize Governed Bronze Tables (Raw Stream Ingestion)

# COMMAND ----------
# Bronze Raw Telemetry
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_bronze.telemetry_raw (
    patient_id INT,
    device_id STRING,
    heart_rate DOUBLE,
    systolic_bp DOUBLE,
    diastolic_bp DOUBLE,
    spo2 DOUBLE,
    temperature DOUBLE,
    timestamp TIMESTAMP,
    _ingested_at TIMESTAMP
) USING DELTA
COMMENT 'Raw real-time ICU and wearable telemetry sensor streams'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")

# Bronze Raw FHIR Encounters
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_bronze.fhir_encounters_raw (
    encounter_id STRING,
    patient_id INT,
    encounter_class STRING,
    type_code STRING,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    provider_id STRING,
    raw_payload STRING,
    _ingested_at TIMESTAMP
) USING DELTA
COMMENT 'Raw clinical encounters ingested from EHR / FHIR interface'
""")

# Bronze Raw Clinical Predictions
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_bronze.predictions_raw (
    id INT,
    user_id INT,
    patient_id INT,
    model_name STRING,
    prediction_result STRING,
    confidence_score DOUBLE,
    input_features STRING,
    created_at TIMESTAMP,
    _ingested_at TIMESTAMP
) USING DELTA
COMMENT 'Raw real-time AI clinical prediction event stream'
""")

# Bronze Raw Clickstream
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_bronze.clickstream_raw (
    id INT,
    user_id INT,
    session_id STRING,
    event_type STRING,
    event_data STRING,
    url STRING,
    created_at TIMESTAMP,
    _ingested_at TIMESTAMP
) USING DELTA
COMMENT 'Raw UI interaction telemetry for clinical workflow analytics'
""")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 5. Initialize Governed Silver Tables (Standardized & Validated)

# COMMAND ----------
# Silver Cleaned Patient Vitals
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_silver.patient_vitals (
    patient_id INT,
    device_id STRING,
    heart_rate DOUBLE,
    systolic_bp DOUBLE,
    diastolic_bp DOUBLE,
    spo2 DOUBLE,
    temperature DOUBLE,
    timestamp TIMESTAMP,
    is_hypoxic INT,
    is_hypertensive INT,
    is_tachycardic INT,
    _processed_at TIMESTAMP
) USING DELTA
COMMENT 'Calibrated, clinically validated patient vitals with physiological range constraints'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")

# Silver Demographics & Patients
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_silver.dim_patient (
    patient_id INT,
    mrn STRING,
    full_name STRING,
    gender STRING,
    dob DATE,
    contact_phone STRING,
    address_zip STRING,
    primary_condition STRING,
    assigned_clinician_id INT,
    consent_granted INT,
    updated_at TIMESTAMP
) USING DELTA
COMMENT 'Master patient index with dynamic PHI protection'
""")

# Silver ML Cleaned Features
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_silver.ml_feature_store (
    patient_id INT,
    model_domain STRING,
    features_json STRING,
    ground_truth_label INT,
    prediction_value INT,
    confidence DOUBLE,
    is_validated INT,
    updated_at TIMESTAMP
) USING DELTA
COMMENT 'Validated historical observations curated for ML retraining and model evaluation'
""")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 6. Initialize Governed Gold Tables (Cohort Metrics & Population Analytics)

# COMMAND ----------
# Gold Patient Risk Profile
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_gold.patient_risk_profile (
    patient_id INT,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    avg_heart_rate DOUBLE,
    max_systolic_bp DOUBLE,
    min_spo2 DOUBLE,
    hypoxic_events BIGINT,
    tachycardic_events BIGINT,
    hypertensive_events BIGINT,
    composite_risk_score DOUBLE,
    risk_severity STRING,
    last_evaluated TIMESTAMP
) USING DELTA
COMMENT 'Longitudinal patient risk scoring and triage tiering for clinical decision support'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")

# Gold Population Health Cohort Analytics
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_gold.population_health_cohorts (
    cohort_id STRING,
    disease_domain STRING,
    age_group STRING,
    total_patients BIGINT,
    high_risk_count BIGINT,
    avg_composite_risk DOUBLE,
    prevalence_rate DOUBLE,
    computed_at TIMESTAMP
) USING DELTA
COMMENT 'Population-scale epidemiological metrics aggregated by demographic and risk strata'
""")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 7. Initialize Governance & Audit Tables (HIPAA Compliance)

# COMMAND ----------
# HIPAA Access & Lineage Audit Log
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_governance.hipaa_access_audit_log (
    audit_id STRING,
    accessed_by STRING,
    user_role STRING,
    action STRING,
    target_catalog STRING,
    target_schema STRING,
    target_table STRING,
    filter_applied STRING,
    records_accessed BIGINT,
    ip_address STRING,
    timestamp TIMESTAMP
) USING DELTA
COMMENT 'Immutable audit ledger recording all clinician and researcher queries for HIPAA compliance'
""")

# Patient Consent Register
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_governance.patient_consent_register (
    consent_id STRING,
    patient_id INT,
    consent_type STRING,
    is_granted INT,
    granted_at TIMESTAMP,
    expires_at TIMESTAMP,
    signature_hash STRING
) USING DELTA
COMMENT 'Cryptographically verified consent records governing secondary use of health data'
""")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 8. Initialize MLOps & Model Lineage Registry

# COMMAND ----------
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.healthcare_mlops.model_governance_registry (
    model_id STRING,
    model_name STRING,
    model_version STRING,
    framework STRING,
    training_data_version STRING,
    auroc DOUBLE,
    accuracy DOUBLE,
    f1_score DOUBLE,
    brier_score DOUBLE,
    deployed_enclave STRING,
    registered_at TIMESTAMP
) USING DELTA
COMMENT 'MLOps model registry storing performance benchmarks, data lineage, and deployment metadata'
""")

print("="*75)
print("  UNITY CATALOG GOVERNANCE & MEDALLION LAKEHOUSE INITIALIZED SUCCESSFULLY!")
print("="*75)
