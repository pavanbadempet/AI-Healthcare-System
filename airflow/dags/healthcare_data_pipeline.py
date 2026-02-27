"""
Airflow DAG for Healthcare Data Pipeline
Focus: ETL/ELT processes, data quality, and monitoring
AI components: ML predictions as enrichment step
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.redis.hooks.redis import RedisHook
from airflow.providers.spark.operators.spark_submit import SparkSubmitOperator
from airflow.sensors.sql import SqlSensor
from airflow.utils.dates import days_ago
from airflow.models import Variable
import json
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Default arguments for DAG
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': days_ago(1),
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
    import requests
    import pandas as pd
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    
    # Get database connection
    postgres_hook = PostgresHook(postgres_conn_id='healthcare_postgres')
    
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
    
    # Store in Redis for downstream tasks
    redis_hook = RedisHook(redis_conn_id='healthcare_redis')
    redis_hook.get_conn().setex(
        f"patient_data:{context['ds']}", 
        3600, 
        df.to_json()
    )
    
    return len(df)

def extract_lab_results(**context):
    """Extract lab results data"""
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    
    postgres_hook = PostgresHook(postgres_conn_id='healthcare_postgres')
    
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
    
    # Store in Redis
    redis_hook = RedisHook(redis_conn_id='healthcare_redis')
    redis_hook.get_conn().setex(
        f"lab_results:{context['ds']}", 
        3600, 
        df.to_json()
    )
    
    return len(df)

def extract_claims_data(**context):
    """Extract claims data"""
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    
    postgres_hook = PostgresHook(postgres_conn_id='healthcare_postgres')
    
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
    
    # Store in Redis
    redis_hook = RedisHook(redis_conn_id='healthcare_redis')
    redis_hook.get_conn().setex(
        f"claims_data:{context['ds']}", 
        3600, 
        df.to_json()
    )
    
    return len(df)

def transform_and_clean_data(**context):
    """Transform and clean extracted data"""
    import pandas as pd
    import numpy as np
    from airflow.providers.redis.hooks.redis import RedisHook
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    
    redis_hook = RedisHook(redis_conn_id='healthcare_redis')
    redis_conn = redis_hook.get_conn()
    
    # Get extracted data
    patients_df = pd.read_json(redis_conn.get(f"patient_data:{context['ds']}"))
    lab_results_df = pd.read_json(redis_conn.get(f"lab_results:{context['ds']}"))
    claims_df = pd.read_json(redis_conn.get(f"claims_data:{context['ds']}"))
    
    transformations = []
    
    # Clean patient data
    if not patients_df.empty:
        # Remove duplicates
        patients_df = patients_df.drop_duplicates(subset=['patient_id'])
        
        # Standardize phone numbers
        patients_df['phone'] = patients_df['phone'].str.replace(r'[^\d]', '', regex=True)
        
        # Validate email format
        patients_df = patients_df[patients_df['email'].str.contains('@', na=False)]
        
        # Convert dates
        patients_df['date_of_birth'] = pd.to_datetime(patients_df['date_of_birth'])
        
        transformations.append(f"Cleaned {len(patients_df)} patient records")
    
    # Clean lab results
    if not lab_results_df.empty:
        # Remove duplicates
        lab_results_df = lab_results_df.drop_duplicates(subset=['result_id'])
        
        # Validate result values (numeric)
        lab_results_df['result_value'] = pd.to_numeric(lab_results_df['result_value'], errors='coerce')
        
        # Remove invalid results
        lab_results_df = lab_results_df.dropna(subset=['result_value'])
        
        # Convert dates
        lab_results_df['test_date'] = pd.to_datetime(lab_results_df['test_date'])
        
        transformations.append(f"Cleaned {len(lab_results_df)} lab result records")
    
    # Clean claims data
    if not claims_df.empty:
        # Remove duplicates
        claims_df = claims_df.drop_duplicates(subset=['claim_id'])
        
        # Validate amounts
        for amount_col in ['billed_amount', 'allowed_amount', 'paid_amount']:
            claims_df[amount_col] = pd.to_numeric(claims_df[amount_col], errors='coerce')
        
        # Remove invalid amounts
        claims_df = claims_df.dropna(subset=['billed_amount'])
        
        # Convert dates
        claims_df['service_date'] = pd.to_datetime(claims_df['service_date'])
        claims_df['submission_date'] = pd.to_datetime(claims_df['submission_date'])
        
        transformations.append(f"Cleaned {len(claims_df)} claims records")
    
    # Store cleaned data
    redis_conn.setex(f"cleaned_patients:{context['ds']}", 3600, patients_df.to_json())
    redis_conn.setex(f"cleaned_lab_results:{context['ds']}", 3600, lab_results_df.to_json())
    redis_conn.setex(f"cleaned_claims:{context['ds']}", 3600, claims_df.to_json())
    
    logger.info(f"Data transformations: {', '.join(transformations)}")
    
    return transformations

def enrich_with_ml_predictions(**context):
    """Enrich data with ML predictions"""
    import pandas as pd
    import numpy as np
    from airflow.providers.redis.hooks.redis import RedisHook
    import joblib
    import os
    
    redis_hook = RedisHook(redis_conn_id='healthcare_redis')
    redis_conn = redis_hook.get_conn()
    
    # Get cleaned lab results
    lab_results_df = pd.read_json(redis_conn.get(f"cleaned_lab_results:{context['ds']}"))
    
    if lab_results_df.empty:
        logger.info("No lab results to enrich")
        return 0
    
    # Load ML models
    try:
        diabetes_model = joblib.load('/opt/airflow/models/Diabetes_Model.pkl')
        heart_model = joblib.load('/opt/airflow/models/Heart_Disease_Model.pkl')
        
        predictions = []
        
        # Process lab results for diabetes prediction
        diabetes_lab_data = lab_results_df[lab_results_df['test_code'].isin(['GLU', 'HBA1C', 'BMI'])]
        if not diabetes_lab_data.empty:
            # Feature engineering for diabetes
            features = prepare_diabetes_features(diabetes_lab_data)
            diabetes_predictions = diabetes_model.predict_proba(features)
            
            # Add predictions to dataframe
            enriched_data = diabetes_lab_data.copy()
            enriched_data['diabetes_risk_score'] = diabetes_predictions[:, 1]  # Probability of diabetes
            predictions.append(f"Generated {len(enriched_data)} diabetes risk predictions")
        
        # Process lab results for heart disease prediction
        heart_lab_data = lab_results_df[lab_results_df['test_code'].isin(['CHOL', 'HDL', 'LDL', 'TRIG', 'BP'])]
        if not heart_lab_data.empty:
            # Feature engineering for heart disease
            features = prepare_heart_features(heart_lab_data)
            heart_predictions = heart_model.predict_proba(features)
            
            # Add predictions to dataframe
            enriched_heart_data = heart_lab_data.copy()
            enriched_heart_data['heart_disease_risk_score'] = heart_predictions[:, 1]
            predictions.append(f"Generated {len(enriched_heart_data)} heart disease risk predictions")
        
        # Store enriched data
        redis_conn.setex(f"enriched_lab_results:{context['ds']}", 3600, enriched_data.to_json())
        
        logger.info(f"ML enrichment: {', '.join(predictions)}")
        return len(predictions)
        
    except Exception as e:
        logger.error(f"ML enrichment failed: {e}")
        return 0

def prepare_diabetes_features(df):
    """Prepare features for diabetes prediction"""
    features = []
    
    for _, row in df.iterrows():
        feature_vector = [
            row.get('result_value', 0),  # glucose or other lab value
            25.0,  # BMI placeholder - would get from patient data
            45,    # Age placeholder
            100,   # Insulin placeholder
            120    # Blood pressure placeholder
        ]
        features.append(feature_vector)
    
    return np.array(features)

def prepare_heart_features(df):
    """Prepare features for heart disease prediction"""
    features = []
    
    for _, row in df.iterrows():
        feature_vector = [
            45,    # Age placeholder
            1,     # Sex placeholder
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
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    
    postgres_hook = PostgresHook(postgres_conn_id='healthcare_warehouse')
    
    # Get enriched data
    redis_hook = RedisHook(redis_conn_id='healthcare_redis')
    redis_conn = redis_hook.get_conn()
    
    load_results = []
    
    # Load patients
    if redis_conn.exists(f"cleaned_patients:{context['ds']}"):
        patients_df = pd.read_json(redis_conn.get(f"cleaned_patients:{context['ds']}"))
        if not patients_df.empty:
            postgres_hook.insert_rows(
                table='warehouse.patients_dim',
                rows=patients_df.to_dict('records'),
                target_fields=patients_df.columns.tolist()
            )
            load_results.append(f"Loaded {len(patients_df)} patient records")
    
    # Load enriched lab results
    if redis_conn.exists(f"enriched_lab_results:{context['ds']}"):
        lab_results_df = pd.read_json(redis_conn.get(f"enriched_lab_results:{context['ds']}"))
        if not lab_results_df.empty:
            postgres_hook.insert_rows(
                table='warehouse.lab_results_fact',
                rows=lab_results_df.to_dict('records'),
                target_fields=lab_results_df.columns.tolist()
            )
            load_results.append(f"Loaded {len(lab_results_df)} enriched lab result records")
    
    # Load claims
    if redis_conn.exists(f"cleaned_claims:{context['ds']}"):
        claims_df = pd.read_json(redis_conn.get(f"cleaned_claims:{context['ds']}"))
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
    import pandas as pd
    
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

# Task definitions
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
    application='/opt/airflow/spark_jobs/healthcare_data_processing.py',
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

# Task dependencies
[extract_patients_task, extract_lab_results_task, extract_claims_task] >> transform_data_task
transform_data_task >> [ml_enrichment_task, spark_processing_task]
ml_enrichment_task >> load_to_warehouse_task
spark_processing_task >> load_to_warehouse_task
load_to_warehouse_task >> data_quality_task
data_quality_task >> update_metrics_task
