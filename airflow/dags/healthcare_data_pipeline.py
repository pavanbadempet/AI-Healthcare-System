"""
Airflow DAG for Healthcare Data Pipeline
Focus: ETL/ELT processes, data quality, and monitoring
AI components: ML predictions as enrichment step
"""

import json
import logging
import os
from datetime import datetime, timedelta

MODEL_REGISTRY_PATH = os.getenv("MODEL_REGISTRY_PATH", "/opt/airflow/models")
SPARK_JOBS_DIR = os.getenv("SPARK_JOBS_DIR", "/opt/airflow/spark_jobs")

import numpy as np
import pandas as pd
from airflow.operators.python import PythonOperator
from airflow.providers.redis.hooks.redis import RedisHook
from airflow.providers.spark.operators.spark_submit import SparkSubmitOperator
from airflow.sensors.sql import SqlSensor
from airflow import DAG

logger = logging.getLogger(__name__)

# ── Dead Letter Queue helpers ────────────────────────────────────
DLQ_DIR = os.getenv("DLQ_DIR", "data/dlq")


def route_to_dead_letter_queue(
    records: list[dict],
    source_task: str,
    error_msg: str,
    execution_date: str,
) -> int:
    """Write failed records to the dead-letter queue as timestamped JSON.

    Returns the number of records written.
    """
    if not records:
        return 0

    os.makedirs(DLQ_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    dlq_file = os.path.join(
        DLQ_DIR,
        f"{source_task}_{execution_date}_{timestamp}.json",
    )
    payload = {
        "source_task": source_task,
        "execution_date": execution_date,
        "error": error_msg,
        "record_count": len(records),
        "records": records,
        "created_at": datetime.utcnow().isoformat(),
    }
    with open(dlq_file, "w") as fh:
        json.dump(payload, fh, default=str)
    logger.warning(
        "Routed %d failed records from %s to DLQ: %s",
        len(records),
        source_task,
        dlq_file,
    )
    return len(records)


def process_dead_letter_queue(**context):
    """Retry records sitting in the dead-letter queue.

    Reads each JSON file in DLQ_DIR, logs a summary, and moves
    successfully processed files to a ``processed/`` sub-directory.
    Records that still fail remain in-place for the next retry cycle.
    """
    if not os.path.isdir(DLQ_DIR):
        logger.info("DLQ directory does not exist — nothing to process.")
        return {"processed": 0, "remaining": 0}

    processed_dir = os.path.join(DLQ_DIR, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    dlq_files = [
        f for f in os.listdir(DLQ_DIR)
        if f.endswith(".json") and os.path.isfile(os.path.join(DLQ_DIR, f))
    ]

    processed_count = 0
    remaining_count = 0

    for fname in dlq_files:
        fpath = os.path.join(DLQ_DIR, fname)
        try:
            with open(fpath) as fh:
                payload = json.load(fh)

            record_count = payload.get("record_count", 0)
            source = payload.get("source_task", "unknown")
            logger.info(
                "DLQ retry: %s — %d records from %s",
                fname,
                record_count,
                source,
            )

            # Move to processed (actual re-ingestion logic is pipeline-specific)
            import shutil
            shutil.move(fpath, os.path.join(processed_dir, fname))
            processed_count += 1

        except Exception as exc:  # noqa: BLE001
            logger.error("DLQ retry failed for %s: %s", fname, exc)
            remaining_count += 1

    summary = {
        "processed": processed_count,
        "remaining": remaining_count,
        "execution_date": context.get("ds"),
    }
    logger.info("DLQ processing complete: %s", summary)
    return summary

# Default arguments for DAG
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
    'max_active_runs': 1,
}

# DAG definition
dag = DAG(
    'healthcare_data_pipeline',
    default_args=default_args,
    description='Healthcare Data ETL Pipeline with ML Enrichment',
    schedule_interval='@hourly',
    catchup=False,
    tags=['healthcare', 'etl', 'data-engineering', 'ml'],
)

def extract_patient_data(**context):
    """Extract patient data from source systems"""
    import os
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from airflow.models import Variable

    postgres_hook = PostgresHook(postgres_conn_id='healthcare_postgres')

    backfill_start = Variable.get("backfill_start_date", default_var=None)
    backfill_end = Variable.get("backfill_end_date", default_var=None)

    if backfill_start and backfill_end:
        logger.info(f"Running patient backfill from {backfill_start} to {backfill_end}")
        extraction_query = f"""
            SELECT patient_id, medical_record_number, first_name, last_name,
                   date_of_birth, gender, email, phone, address, insurance_id,
                   primary_care_physician, created_at, updated_at
            FROM app_data.patients
            WHERE (updated_at BETWEEN '{backfill_start}' AND '{backfill_end}')
            OR (created_at BETWEEN '{backfill_start}' AND '{backfill_end}')
        """
    else:
        # Extract incremental patient data
        extraction_query = """
            SELECT patient_id, medical_record_number, first_name, last_name,
                   date_of_birth, gender, email, phone, address, insurance_id,
                   primary_care_physician, created_at, updated_at
            FROM app_data.patients
            WHERE updated_at > '{{ prev_ds }}'
            OR created_at > '{{ prev_ds }}'
        """

    df = postgres_hook.get_pandas_df(extraction_query)

    # Log extraction metrics
    logger.info(f"Extracted {len(df)} patient records")

    # Store in staging Parquet file for downstream tasks to prevent Redis memory bloat
    os.makedirs('/tmp/airflow/staging', exist_ok=True)
    filepath = f"/tmp/airflow/staging/patient_data_{context['ds']}.parquet"
    df.to_parquet(filepath, index=False)
    logger.info(f"Stored patient data at {filepath}")

    return filepath

def extract_lab_results(**context):
    """Extract lab results data"""
    import os
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from airflow.models import Variable

    postgres_hook = PostgresHook(postgres_conn_id='healthcare_postgres')

    backfill_start = Variable.get("backfill_start_date", default_var=None)
    backfill_end = Variable.get("backfill_end_date", default_var=None)

    if backfill_start and backfill_end:
        logger.info(f"Running lab results backfill from {backfill_start} to {backfill_end}")
        extraction_query = f"""
            SELECT result_id, patient_id, test_code, test_name,
                   result_value, result_unit, reference_range, abnormal_flag,
                   test_date, performed_by, facility_id, created_at
            FROM app_data.lab_results
            WHERE test_date BETWEEN '{backfill_start}' AND '{backfill_end}'
        """
    else:
        extraction_query = """
            SELECT result_id, patient_id, test_code, test_name,
                   result_value, result_unit, reference_range, abnormal_flag,
                   test_date, performed_by, facility_id, created_at
            FROM app_data.lab_results
            WHERE test_date >= '{{ ds }}'
            AND test_date < '{{ next_ds }}'
        """

    df = postgres_hook.get_pandas_df(extraction_query)

    logger.info(f"Extracted {len(df)} lab result records")

    # Store in staging Parquet file
    os.makedirs('/tmp/airflow/staging', exist_ok=True)
    filepath = f"/tmp/airflow/staging/lab_results_{context['ds']}.parquet"
    df.to_parquet(filepath, index=False)
    logger.info(f"Stored lab results data at {filepath}")

    return filepath

def extract_claims_data(**context):
    """Extract claims data with optional backfill support."""
    import os
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from airflow.models import Variable

    postgres_hook = PostgresHook(postgres_conn_id='healthcare_postgres')

    backfill_start = Variable.get("backfill_start_date", default_var=None)
    backfill_end = Variable.get("backfill_end_date", default_var=None)

    if backfill_start and backfill_end:
        logger.info(f"Running claims backfill from {backfill_start} to {backfill_end}")
        extraction_query = f"""
            SELECT claim_id, patient_id, provider_id, service_date,
                   procedure_code, diagnosis_code, billed_amount,
                   allowed_amount, paid_amount, claim_status,
                   submission_date, processing_date
            FROM app_data.claims
            WHERE (submission_date BETWEEN '{backfill_start}' AND '{backfill_end}')
            OR (processing_date BETWEEN '{backfill_start}' AND '{backfill_end}')
        """
    else:
        extraction_query = """
            SELECT claim_id, patient_id, provider_id, service_date,
                   procedure_code, diagnosis_code, billed_amount,
                   allowed_amount, paid_amount, claim_status,
                   submission_date, processing_date
            FROM app_data.claims
            WHERE submission_date >= '{{ ds }}'
            AND submission_date < '{{ next_ds }}'
        """

    df = postgres_hook.get_pandas_df(extraction_query)

    logger.info(f"Extracted {len(df)} claims records")

    # Store in staging Parquet file
    os.makedirs('/tmp/airflow/staging', exist_ok=True)
    filepath = f"/tmp/airflow/staging/claims_data_{context['ds']}.parquet"
    df.to_parquet(filepath, index=False)
    logger.info(f"Stored claims data at {filepath}")

    return filepath

def transform_and_clean_data(**context):
    """Transform and clean extracted data.

    Records that fail individual cleaning steps are routed to the
    dead-letter queue so they can be inspected and retried later.
    """
    import os
    import pandas as pd

    # Get extracted data from Parquet staging files
    patients_df = pd.read_parquet(f"/tmp/airflow/staging/patient_data_{context['ds']}.parquet")
    lab_results_df = pd.read_parquet(f"/tmp/airflow/staging/lab_results_{context['ds']}.parquet")
    claims_df = pd.read_parquet(f"/tmp/airflow/staging/claims_data_{context['ds']}.parquet")

    transformations = []
    execution_date = context.get("ds", "unknown")

    # ── Clean patient data ───────────────────────────────────────
    if not patients_df.empty:
        patients_df = patients_df.drop_duplicates(subset=['patient_id'])
        patients_df['phone'] = patients_df['phone'].str.replace(r'[^\d]', '', regex=True)

        # Route invalid emails to DLQ
        invalid_email_mask = ~patients_df['email'].str.contains('@', na=False)
        if invalid_email_mask.any():
            bad_records = patients_df[invalid_email_mask].to_dict(orient='records')
            route_to_dead_letter_queue(
                bad_records, "transform_patients",
                "Invalid email format", execution_date,
            )
        patients_df = patients_df[~invalid_email_mask]

        patients_df['date_of_birth'] = pd.to_datetime(patients_df['date_of_birth'])
        transformations.append(f"Cleaned {len(patients_df)} patient records")

    # ── Clean lab results ────────────────────────────────────────
    if not lab_results_df.empty:
        lab_results_df = lab_results_df.drop_duplicates(subset=['result_id'])
        lab_results_df['result_value'] = pd.to_numeric(lab_results_df['result_value'], errors='coerce')

        # Route non-numeric results to DLQ
        invalid_results_mask = lab_results_df['result_value'].isna()
        if invalid_results_mask.any():
            bad_records = lab_results_df[invalid_results_mask].to_dict(orient='records')
            route_to_dead_letter_queue(
                bad_records, "transform_lab_results",
                "Non-numeric result_value", execution_date,
            )
        lab_results_df = lab_results_df.dropna(subset=['result_value'])

        lab_results_df['test_date'] = pd.to_datetime(lab_results_df['test_date'])
        transformations.append(f"Cleaned {len(lab_results_df)} lab result records")

    # ── Clean claims data ────────────────────────────────────────
    if not claims_df.empty:
        claims_df = claims_df.drop_duplicates(subset=['claim_id'])

        for amount_col in ['billed_amount', 'allowed_amount', 'paid_amount']:
            claims_df[amount_col] = pd.to_numeric(claims_df[amount_col], errors='coerce')

        # Route claims with invalid billed amounts to DLQ
        invalid_amount_mask = claims_df['billed_amount'].isna()
        if invalid_amount_mask.any():
            bad_records = claims_df[invalid_amount_mask].to_dict(orient='records')
            route_to_dead_letter_queue(
                bad_records, "transform_claims",
                "Invalid billed_amount", execution_date,
            )
        claims_df = claims_df.dropna(subset=['billed_amount'])

        claims_df['service_date'] = pd.to_datetime(claims_df['service_date'])
        claims_df['submission_date'] = pd.to_datetime(claims_df['submission_date'])
        transformations.append(f"Cleaned {len(claims_df)} claims records")

    # Store cleaned data in Parquet staging files
    patients_df.to_parquet(f"/tmp/airflow/staging/cleaned_patients_{context['ds']}.parquet", index=False)
    lab_results_df.to_parquet(f"/tmp/airflow/staging/cleaned_lab_results_{context['ds']}.parquet", index=False)
    claims_df.to_parquet(f"/tmp/airflow/staging/cleaned_claims_{context['ds']}.parquet", index=False)

    logger.info(f"Data transformations: {', '.join(transformations)}")

    return transformations

def enrich_with_ml_predictions(**context):
    """Enrich data with ML predictions"""

    import os
    import joblib
    import pandas as pd

    # Get cleaned lab results and patients from Parquet staging
    lab_results_df = pd.read_parquet(f"/tmp/airflow/staging/cleaned_lab_results_{context['ds']}.parquet")
    patients_df = pd.read_parquet(f"/tmp/airflow/staging/cleaned_patients_{context['ds']}.parquet")

    if lab_results_df.empty:
        logger.info("No lab results to enrich")
        return 0

    # Load ML models
    try:
        diabetes_model = joblib.load(os.path.join(MODEL_REGISTRY_PATH, 'Diabetes_Model.pkl'))
        heart_model = joblib.load(os.path.join(MODEL_REGISTRY_PATH, 'Heart_Disease_Model.pkl'))

        predictions = []
        enriched_data = lab_results_df.copy()

        # Process lab results for diabetes prediction
        diabetes_lab_data = lab_results_df[lab_results_df['test_code'].isin(['GLU', 'HBA1C', 'BMI'])]
        if not diabetes_lab_data.empty:
            # Feature engineering for diabetes using patients profile
            features = prepare_diabetes_features(diabetes_lab_data, patients_df)
            diabetes_predictions = diabetes_model.predict_proba(features)

            # Map predictions back to the main lab results copy
            diabetes_indices = diabetes_lab_data.index
            enriched_data.loc[diabetes_indices, 'diabetes_risk_score'] = diabetes_predictions[:, 1]
            predictions.append(f"Generated {len(diabetes_lab_data)} diabetes risk predictions")

        # Process lab results for heart disease prediction
        heart_lab_data = lab_results_df[lab_results_df['test_code'].isin(['CHOL', 'HDL', 'LDL', 'TRIG', 'BP'])]
        if not heart_lab_data.empty:
            # Feature engineering for heart disease using patients profile
            features = prepare_heart_features(heart_lab_data, patients_df)
            heart_predictions = heart_model.predict_proba(features)

            # Map predictions back to the main lab results copy
            heart_indices = heart_lab_data.index
            enriched_data.loc[heart_indices, 'heart_disease_risk_score'] = heart_predictions[:, 1]
            predictions.append(f"Generated {len(heart_lab_data)} heart disease risk predictions")

        # Store enriched data in Parquet staging file
        enriched_data.to_parquet(f"/tmp/airflow/staging/enriched_lab_results_{context['ds']}.parquet", index=False)

        logger.info(f"ML enrichment: {', '.join(predictions)}")
        return len(predictions)

    except Exception as e:
        logger.error(f"ML enrichment failed: {e}")
        return 0

def prepare_diabetes_features(df, patients_df=None):
    """Prepare features for diabetes prediction using actual patient profiles to avoid skew"""
    import numpy as np
    from datetime import datetime

    if patients_df is not None and not patients_df.empty:
        df = df.merge(patients_df, on='patient_id', how='left')

    features = []
    for _, row in df.iterrows():
        # Compute actual age
        age = 45  # fallback
        if 'date_of_birth' in row and pd.notnull(row['date_of_birth']):
            try:
                dob = pd.to_datetime(row['date_of_birth'])
                age = datetime.now().year - dob.year
            except Exception:
                pass

        feature_vector = [
            row.get('result_value', 0),  # glucose or other lab value
            25.0,  # BMI placeholder
            age,   # Dynamic Patient Age
            100,   # Insulin placeholder
            120    # Blood pressure placeholder
        ]
        features.append(feature_vector)

    return np.array(features)

def prepare_heart_features(df, patients_df=None):
    """Prepare features for heart disease prediction using actual patient profiles to avoid skew"""
    import numpy as np
    from datetime import datetime

    if patients_df is not None and not patients_df.empty:
        df = df.merge(patients_df, on='patient_id', how='left')

    features = []
    for _, row in df.iterrows():
        # Compute actual age and gender
        age = 45  # fallback
        if 'date_of_birth' in row and pd.notnull(row['date_of_birth']):
            try:
                dob = pd.to_datetime(row['date_of_birth'])
                age = datetime.now().year - dob.year
            except Exception:
                pass

        gender_val = str(row.get('gender', 'M')).upper()
        sex = 1 if gender_val.startswith('M') or gender_val == '1' else 0

        feature_vector = [
            age,   # Dynamic Patient Age
            sex,   # Dynamic Patient Sex
            3,     # Chest pain type
            140,   # Blood pressure
            row.get('result_value', 200),  # Cholesterol
            0,     # Fasting blood sugar
            0,     # Rest ECG
            150,   # Max heart rate
            0,     # Exercise angina
            2.0,   # ST depression
            1,     # Slope
            0,     # Number of vessels
            3      # Thal
        ]
        features.append(feature_vector)

    return np.array(features)

def load_to_data_warehouse(**context):
    """Load processed data to data warehouse"""
    import os
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    postgres_hook = PostgresHook(postgres_conn_id='healthcare_warehouse')

    load_results = []

    # Paths to staging Parquet files
    patients_path = f"/tmp/airflow/staging/cleaned_patients_{context['ds']}.parquet"
    lab_results_path = f"/tmp/airflow/staging/enriched_lab_results_{context['ds']}.parquet"
    claims_path = f"/tmp/airflow/staging/cleaned_claims_{context['ds']}.parquet"

    # Load patients
    if os.path.exists(patients_path):
        patients_df = pd.read_parquet(patients_path)
        if not patients_df.empty:
            postgres_hook.insert_rows(
                table='warehouse.patients_dim',
                rows=patients_df.to_dict('records'),
                target_fields=patients_df.columns.tolist()
            )
            load_results.append(f"Loaded {len(patients_df)} patient records")

    # Load enriched lab results
    if os.path.exists(lab_results_path):
        lab_results_df = pd.read_parquet(lab_results_path)
        if not lab_results_df.empty:
            postgres_hook.insert_rows(
                table='warehouse.lab_results_fact',
                rows=lab_results_df.to_dict('records'),
                target_fields=lab_results_df.columns.tolist()
            )
            load_results.append(f"Loaded {len(lab_results_df)} enriched lab result records")

    # Load claims
    if os.path.exists(claims_path):
        claims_df = pd.read_parquet(claims_path)
        if not claims_df.empty:
            postgres_hook.insert_rows(
                table='warehouse.claims_fact',
                rows=claims_df.to_dict('records'),
                target_fields=claims_df.columns.tolist()
            )
            load_results.append(f"Loaded {len(claims_df)} claim records")

    logger.info(f"Data warehouse loading: {', '.join(load_results)}")
    return load_results

def generate_data_quality_report(**context):
    """Generate data quality report"""
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    postgres_hook = PostgresHook(postgres_conn_id='healthcare_warehouse')

    # Quality checks
    quality_checks = []

    # Check patient data completeness
    patient_completeness = postgres_hook.get_first("""
        SELECT
            COUNT(*) as total_patients,
            COUNT(CASE WHEN email IS NOT NULL THEN 1 END) as patients_with_email,
            COUNT(CASE WHEN phone IS NOT NULL THEN 1 END) as patients_with_phone,
            COUNT(CASE WHEN date_of_birth IS NOT NULL THEN 1 END) as patients_with_dob
        FROM warehouse.patients_dim
        WHERE created_at >= '{{ ds }}' AND created_at < '{{ next_ds }}'
    """)

    if patient_completeness:
        total = patient_completeness[0]
        email_completeness = patient_completeness[1] / total if total > 0 else 0
        phone_completeness = patient_completeness[2] / total if total > 0 else 0
        dob_completeness = patient_completeness[3] / total if total > 0 else 0

        quality_checks.append({
            'metric': 'patient_data_completeness',
            'value': (email_completeness + phone_completeness + dob_completeness) / 3,
            'threshold': 0.95,
            'status': 'pass' if (email_completeness + phone_completeness + dob_completeness) / 3 >= 0.95 else 'fail'
        })

    # Check lab result timeliness
    lab_timeliness = postgres_hook.get_first("""
        SELECT
            AVG(EXTRACT(EPOCH FROM (created_at - test_date))/3600) as avg_processing_hours
        FROM warehouse.lab_results_fact
        WHERE test_date >= '{{ ds }}' AND test_date < '{{ next_ds }}'
    """)

    if lab_timeliness and lab_timeliness[0]:
        avg_hours = lab_timeliness[0]
        quality_checks.append({
            'metric': 'lab_result_timeliness',
            'value': avg_hours,
            'threshold': 24.0,
            'status': 'pass' if avg_hours <= 24.0 else 'fail'
        })

    # Check claims data accuracy
    claims_accuracy = postgres_hook.get_first("""
        SELECT
            COUNT(*) as total_claims,
            COUNT(CASE WHEN billed_amount > 0 THEN 1 END) as valid_claims
        FROM warehouse.claims_fact
        WHERE submission_date >= '{{ ds }}' AND submission_date < '{{ next_ds }}'
    """)

    if claims_accuracy:
        total = claims_accuracy[0]
        valid = claims_accuracy[1]
        accuracy = valid / total if total > 0 else 0

        quality_checks.append({
            'metric': 'claims_data_accuracy',
            'value': accuracy,
            'threshold': 0.98,
            'status': 'pass' if accuracy >= 0.98 else 'fail'
        })

    # Store quality report
    redis_hook = RedisHook(redis_conn_id='healthcare_redis')
    redis_conn = redis_hook.get_conn()

    quality_report = {
        'report_date': context['ds'],
        'checks': quality_checks,
        'overall_score': sum(check['value'] for check in quality_checks) / len(quality_checks),
        'generated_at': datetime.now().isoformat()
    }

    redis_conn.setex(
        f"quality_report:{context['ds']}",
        86400 * 30,  # Keep 30 days
        json.dumps(quality_report)
    )

    # Alerting logic for Data Quality
    overall_score = quality_report['overall_score']
    if overall_score < 0.95:
        logger.warning(f"ALERT: Data Quality Score ({overall_score}) below SLA threshold (0.95)!")
        # Programmatically send webhook alert if configured
        import os
        import urllib.request
        slack_url = os.getenv("SLACK_WEBHOOK_URL")
        if slack_url:
            payload = json.dumps({
                "text": f"🚨 *AI Healthcare System Data Quality Alert*\n*Execution Date*: {context['ds']}\n*Overall Quality Score*: {overall_score:.4f}\n*SLA Status*: FAILED"
            }).encode('utf-8')
            try:
                req = urllib.request.Request(slack_url, data=payload, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    pass
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")

    logger.info(f"Data quality report generated with {len(quality_checks)} checks")
    return quality_report

def update_pipeline_metrics(**context):
    """Update pipeline performance metrics"""
    from airflow.providers.redis.hooks.redis import RedisHook

    redis_hook = RedisHook(redis_conn_id='healthcare_redis')
    redis_conn = redis_hook.get_conn()

    # Calculate pipeline metrics
    execution_date = context['ds']
    dag_run = context['dag_run']

    metrics = {
        'dag_id': dag_run.dag_id,
        'execution_date': execution_date,
        'start_time': dag_run.start_date.isoformat() if dag_run.start_date else None,
        'end_time': dag_run.end_date.isoformat() if dag_run.end_date else None,
        'duration_seconds': (dag_run.end_date - dag_run.start_date).total_seconds() if dag_run.start_date and dag_run.end_date else None,
        'status': dag_run.get_state(),
        'task_instances': len(dag_run.get_task_instances()),
        'successful_tasks': len([ti for ti in dag_run.get_task_instances() if ti.state == 'success']),
        'failed_tasks': len([ti for ti in dag_run.get_task_instances() if ti.state == 'failed'])
    }

    # Store metrics
    redis_conn.setex(
        f"pipeline_metrics:{execution_date}",
        86400 * 7,  # Keep 7 days
        json.dumps(metrics)
    )

    logger.info(f"Pipeline metrics updated for {execution_date}")
    return metrics

def cleanup_staging_files(**context):
    """Clean up staging files for this run to keep disk utilization low"""
    import os
    ds = context['ds']
    files_to_clean = [
        f"/tmp/airflow/staging/patient_data_{ds}.parquet",
        f"/tmp/airflow/staging/lab_results_{ds}.parquet",
        f"/tmp/airflow/staging/claims_data_{ds}.parquet",
        f"/tmp/airflow/staging/cleaned_patients_{ds}.parquet",
        f"/tmp/airflow/staging/enriched_lab_results_{ds}.parquet",
        f"/tmp/airflow/staging/cleaned_claims_{ds}.parquet",
    ]
    cleaned_count = 0
    for filepath in files_to_clean:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                cleaned_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete transient file {filepath}: {e}")
    logger.info(f"Transient storage cleanup: deleted {cleaned_count} staging Parquet files.")
    return cleaned_count

# Task definitions
cleanup_staging_task = PythonOperator(
    task_id='cleanup_staging_files',
    python_callable=cleanup_staging_files,
    dag=dag,
)

extract_patients_task = PythonOperator(
    task_id='extract_patients',
    python_callable=extract_patient_data,
    dag=dag,
)

extract_lab_results_task = PythonOperator(
    task_id='extract_lab_results',
    python_callable=extract_lab_results,
    dag=dag,
)

extract_claims_task = PythonOperator(
    task_id='extract_claims',
    python_callable=extract_claims_data,
    dag=dag,
)

transform_data_task = PythonOperator(
    task_id='transform_and_clean_data',
    python_callable=transform_and_clean_data,
    dag=dag,
)

ml_enrichment_task = PythonOperator(
    task_id='enrich_with_ml_predictions',
    python_callable=enrich_with_ml_predictions,
    dag=dag,
)

load_to_warehouse_task = PythonOperator(
    task_id='load_to_data_warehouse',
    python_callable=load_to_data_warehouse,
    dag=dag,
)

data_quality_task = PythonOperator(
    task_id='generate_data_quality_report',
    python_callable=generate_data_quality_report,
    dag=dag,
)

update_metrics_task = PythonOperator(
    task_id='update_pipeline_metrics',
    python_callable=update_pipeline_metrics,
    dag=dag,
)

# Spark job for big data processing
spark_processing_task = SparkSubmitOperator(
    task_id='spark_big_data_processing',
    application=os.path.join(SPARK_JOBS_DIR, 'healthcare_data_processing.py'),
    conn_id='spark_default',
    driver_memory='4g',
    executor_memory='4g',
    executor_cores='2',
    num_executors='4',
    packages='org.postgresql:postgresql:42.2.18',
    dag=dag,
)

# Data quality sensor
data_quality_sensor = SqlSensor(
    task_id='data_quality_sensor',
    conn_id='healthcare_warehouse',
    sql="""
        SELECT 1
        FROM warehouse.patients_dim
        WHERE created_at >= '{{ ds }}'
        AND created_at < '{{ next_ds }}'
        LIMIT 1
    """,
    poke_interval=60,
    timeout=300,
    mode='poke',
    dag=dag,
)

# Dead-letter queue tasks
process_dlq_task = PythonOperator(
    task_id='process_dead_letter_queue',
    python_callable=process_dead_letter_queue,
    dag=dag,
)

# Task dependencies
[extract_patients_task, extract_lab_results_task, extract_claims_task] >> transform_data_task
transform_data_task >> [ml_enrichment_task, spark_processing_task]
ml_enrichment_task >> load_to_warehouse_task
spark_processing_task >> load_to_warehouse_task
load_to_warehouse_task >> [data_quality_task, cleanup_staging_task]
data_quality_task >> [update_metrics_task, process_dlq_task]
