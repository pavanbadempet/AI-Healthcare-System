# ===========================================================
# AI Healthcare System - Model Retraining Pipeline
# ===========================================================
# Simple, clean ETL using PySpark + Airflow
# Schedule: Weekly on Sundays at 2 AM
# ===========================================================

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago
import logging
import os

logger = logging.getLogger(__name__)

# --- DAG Config ---
default_args = {
    'owner': 'healthcare-team',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    dag_id='model_retraining_pipeline',
    default_args=default_args,
    description='Weekly model retraining with PySpark ETL',
    schedule_interval='0 2 * * 0',
    start_date=days_ago(1),
    catchup=False,
    tags=['ml', 'pyspark', 'etl'],
)

STAGING_DIR = '/tmp/airflow/staging'


# ===========================================================
# TASK 1: Extract - Pull data from PostgreSQL using PySpark
# ===========================================================
def extract_data(**context):
    """Extract health records using PySpark JDBC."""
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder \
        .appName("HealthcareETL-Extract") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()
    
    db_url = os.getenv('DATABASE_URL', '')
    
    # Skip if no PostgreSQL configured
    if 'postgresql' not in db_url and 'postgres' not in db_url:
        logger.info("No PostgreSQL configured, skipping extraction")
        spark.stop()
        return 0
    
    try:
        # Spark JDBC read with partitioning
        df = spark.read \
            .format("jdbc") \
            .option("url", f"jdbc:postgresql://{db_url.split('@')[1]}") \
            .option("query", """
                SELECT record_type, data, prediction 
                FROM health_records hr
                JOIN users u ON hr.user_id = u.id
                WHERE u.allow_data_collection = 1
            """) \
            .option("driver", "org.postgresql.Driver") \
            .load()
        
        count = df.count()
        os.makedirs(STAGING_DIR, exist_ok=True)
        df.write.mode('overwrite').parquet(f'{STAGING_DIR}/raw_data.parquet')
        
        logger.info(f"Extracted {count} records")
        spark.stop()
        return count
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        spark.stop()
        return 0


# ===========================================================
# TASK 2: Transform - Feature engineering with Spark SQL
# ===========================================================
def transform_data(**context):
    """Transform data using Spark DataFrame operations."""
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, get_json_object, when
    
    staging_path = f'{STAGING_DIR}/raw_data.parquet'
    if not os.path.exists(staging_path):
        logger.info("No data to transform")
        return {}
    
    spark = SparkSession.builder.appName("HealthcareETL-Transform").getOrCreate()
    
    df = spark.read.parquet(staging_path)
    
    # Parse JSON and add label
    transformed = df \
        .withColumn('age', get_json_object('data', '$.age').cast('float')) \
        .withColumn('bmi', get_json_object('data', '$.bmi').cast('float')) \
        .withColumn('label', when(col('prediction').contains('High'), 1).otherwise(0)) \
        .select('record_type', 'age', 'bmi', 'label')
    
    # Write by record type
    counts = {}
    for rtype in ['diabetes', 'heart', 'liver']:
        subset = transformed.filter(col('record_type') == rtype)
        cnt = subset.count()
        if cnt > 0:
            subset.write.mode('overwrite').parquet(f'{STAGING_DIR}/{rtype}_features.parquet')
        counts[rtype] = cnt
    
    logger.info(f"Transformed: {counts}")
    spark.stop()
    return counts


# ===========================================================
# TASK 3: Train - Retrain models
# ===========================================================
def train_models(**context):
    """Retrain models using existing training scripts."""
    import subprocess
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    results = {}
    
    for model in ['diabetes', 'heart', 'liver']:
        script = f'{base_dir}/backend/train_{model}.py'
        if os.path.exists(script):
            result = subprocess.run(['python', script], capture_output=True, timeout=1800)
            results[model] = 'success' if result.returncode == 0 else 'failed'
        else:
            results[model] = 'skipped'
    
    logger.info(f"Training results: {results}")
    return results


# ===========================================================
# TASK 4: Validate - Check if deployment should proceed
# ===========================================================
def validate_models(**context):
    """Decide whether to deploy based on training success."""
    results = context['ti'].xcom_pull(task_ids='train')
    
    success_count = sum(1 for v in results.values() if v == 'success')
    should_deploy = success_count > 0
    
    logger.info(f"Validation: {success_count} models succeeded, deploy={should_deploy}")
    return 'deploy' if should_deploy else 'skip'


# ===========================================================
# TASK 5: Deploy - Reload models via API
# ===========================================================
def deploy_models(**context):
    """Call model reload endpoint."""
    import requests
    
    backend = os.getenv('BACKEND_URL', 'http://localhost:8000')
    token = os.getenv('ADMIN_JWT_TOKEN')
    
    if not token:
        logger.warning("No admin token, skipping deployment")
        return
    
    try:
        resp = requests.post(
            f"{backend}/admin/reload_models",
            headers={'Authorization': f'Bearer {token}'},
            timeout=30
        )
        logger.info(f"Deploy response: {resp.status_code}")
    except Exception as e:
        logger.error(f"Deploy failed: {e}")


# ===========================================================
# DAG Structure
# ===========================================================
start = EmptyOperator(task_id='start', dag=dag)
extract = PythonOperator(task_id='extract', python_callable=extract_data, dag=dag)
transform = PythonOperator(task_id='transform', python_callable=transform_data, dag=dag)
train = PythonOperator(task_id='train', python_callable=train_models, dag=dag)
validate = BranchPythonOperator(task_id='validate', python_callable=validate_models, dag=dag)
deploy = PythonOperator(task_id='deploy', python_callable=deploy_models, dag=dag)
skip = EmptyOperator(task_id='skip', dag=dag)
end = EmptyOperator(task_id='end', trigger_rule='none_failed_min_one_success', dag=dag)

# Pipeline: start -> extract -> transform -> train -> validate -> [deploy|skip] -> end
start >> extract >> transform >> train >> validate >> [deploy, skip] >> end
