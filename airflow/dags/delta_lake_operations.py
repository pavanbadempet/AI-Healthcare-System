"""
Airflow DAG for Databricks Delta Lake Operations
Liquid Clustering, Time Travel, CDC, and Healthcare-Specific Pipelines
"""

import logging
import os
from datetime import datetime, timedelta

SPARK_JOBS_DIR = os.getenv("SPARK_JOBS_DIR", "/opt/airflow/spark_jobs")

from airflow.operators.python import PythonOperator
from airflow.providers.spark.operators.spark_submit import SparkSubmitOperator

from airflow import DAG

logger = logging.getLogger(__name__)

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

# Shared Spark session builder for Delta Lake + Unity Catalog
def _create_spark(app_name: str):
    import os
    from pyspark.sql import SparkSession
    catalog = os.getenv("DELTA_CATALOG", "uc_healthcare_prod")
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config(f"spark.sql.catalog.{catalog}", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.databricks.delta.schema.autoMerge.enabled", "true") \
        .getOrCreate()

# DAG definition
dag = DAG(
    'delta_lake_healthcare_operations',
    default_args=default_args,
    description='Databricks Delta Lake operations for healthcare data',
    schedule_interval='@daily',
    catchup=False,
    tags=['healthcare', 'delta-lake', 'liquid-clustering', 'cdc', 'unity-catalog'],
)


def create_delta_lab_results(**context):
    """Create Delta Lake table for lab results with Liquid Clustering"""
    from pyspark.sql import types as T
    from pyspark.sql.functions import col, current_timestamp, to_timestamp

    from backend.delta_lake_integration import get_delta_manager

    spark = _create_spark("DeltaLabResults")

    try:
        lab_data = [
            ("R001", "P001", "GLU", "Glucose", 95.5, "mg/dL", "70-100", "N", "2023-01-15 10:30:00", "LabTech1", "F001"),
            ("R002", "P001", "HBA1C", "Hemoglobin A1c", 6.2, "%", "4.0-5.6", "A", "2023-01-15 10:35:00", "LabTech1", "F001"),
            ("R003", "P002", "CHOL", "Cholesterol", 210.0, "mg/dL", "<200", "H", "2023-01-16 09:15:00", "LabTech2", "F001"),
            ("R004", "P003", "BP", "Blood Pressure", 120.0, "mmHg", "90-120", "N", "2023-01-17 14:20:00", "LabTech3", "F002"),
            ("R005", "P002", "TSH", "TSH", 2.1, "mIU/L", "0.4-4.0", "N", "2023-01-18 11:45:00", "LabTech1", "F001"),
        ]

        lab_schema = T.StructType([
            T.StructField("result_id", T.StringType(), False),
            T.StructField("patient_id", T.StringType(), False),
            T.StructField("test_code", T.StringType(), False),
            T.StructField("test_name", T.StringType(), True),
            T.StructField("result_value", T.FloatType(), True),
            T.StructField("result_unit", T.StringType(), True),
            T.StructField("reference_range", T.StringType(), True),
            T.StructField("abnormal_flag", T.StringType(), True),
            T.StructField("test_date", T.StringType(), True),
            T.StructField("performed_by", T.StringType(), True),
            T.StructField("facility_id", T.StringType(), True),
        ])

        lab_df = spark.createDataFrame(lab_data, lab_schema)
        lab_df = lab_df.withColumn("test_date", to_timestamp(col("test_date"), "yyyy-MM-dd HH:mm:ss")) \
                       .withColumn("created_at", current_timestamp())

        delta_manager = get_delta_manager(spark)
        result = delta_manager.create_lab_results_table(lab_df)

        logger.info(f"Created Delta lab results table: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to create Delta lab results table: {e}")
        raise
    finally:
        spark.stop()


def evolve_lab_results_schema(**context):
    """Evolve lab results schema for new test codes via ALTER TABLE"""
    from backend.delta_lake_integration import get_delta_manager

    spark = _create_spark("DeltaSchemaEvolution")

    try:
        new_lab_codes = ["VITD", "IRON", "CALCIUM", "PROTEIN"]
        delta_manager = get_delta_manager(spark)
        result = delta_manager.evolve_lab_results_schema(new_lab_codes)

        logger.info(f"Evolved lab results schema: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to evolve lab results schema: {e}")
        raise
    finally:
        spark.stop()


def create_delta_patient_dimension(**context):
    """Create patient dimension with SCD Type 2 and HIPAA audit columns"""
    from pyspark.sql import types as T
    from pyspark.sql.functions import col, current_timestamp, to_date

    from backend.delta_lake_integration import get_delta_manager

    spark = _create_spark("DeltaPatientDimension")

    try:
        patient_data = [
            ("P001", "John", "Doe", "1980-01-15", "M", "john.doe@email.com", "555-1234", "123 Main St", "A123", "Dr. Smith"),
            ("P002", "Jane", "Smith", "1975-05-22", "F", "jane.smith@email.com", "555-5678", "456 Oak Ave", "B456", "Dr. Johnson"),
            ("P003", "Bob", "Wilson", "1990-12-10", "M", "bob.wilson@email.com", "555-9012", "789 Pine Rd", "C789", "Dr. Brown"),
        ]

        patient_schema = T.StructType([
            T.StructField("patient_id", T.StringType(), False),
            T.StructField("first_name", T.StringType(), True),
            T.StructField("last_name", T.StringType(), True),
            T.StructField("date_of_birth", T.StringType(), True),
            T.StructField("gender", T.StringType(), True),
            T.StructField("email", T.StringType(), True),
            T.StructField("phone", T.StringType(), True),
            T.StructField("address", T.StringType(), True),
            T.StructField("insurance_id", T.StringType(), True),
            T.StructField("primary_care_physician", T.StringType(), True),
        ])

        patient_df = spark.createDataFrame(patient_data, patient_schema)
        patient_df = patient_df.withColumn("created_at", current_timestamp()) \
                               .withColumn("updated_at", current_timestamp()) \
                               .withColumn("updated_date", to_date(col("updated_at")))

        delta_manager = get_delta_manager(spark)
        result = delta_manager.create_patient_dimension(patient_df)

        logger.info(f"Created Delta patient dimension: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to create Delta patient dimension: {e}")
        raise
    finally:
        spark.stop()


def test_time_travel_queries(**context):
    """Test Delta Lake time travel via RESTORE and VERSION AS OF"""
    from backend.delta_lake_integration import get_delta_manager

    spark = _create_spark("DeltaTimeTravel")

    import os
    try:
        delta_manager = get_delta_manager(spark)
        catalog = os.getenv("DELTA_CATALOG", "uc_healthcare_prod")
        database = os.getenv("DELTA_DATABASE", "healthcare_db")
        table_name = f"{catalog}.{database}.lab_results"

        # Get table history
        history = delta_manager.schema_manager.get_table_history(table_name)

        # Test time travel if versions exist
        time_travel_results = []
        if history:
            latest_version = history[0].get("version", 0)
            historical_df = delta_manager.schema_manager.query_at_snapshot(table_name, latest_version)
            time_travel_results.append({
                "version": latest_version,
                "record_count": historical_df.count(),
                "query_time": "historical",
            })

        result = {
            "table_name": table_name,
            "history_count": len(history),
            "time_travel_results": time_travel_results,
            "time_travel_enabled": len(history) > 0,
        }

        logger.info(f"Time travel test results: {result}")
        return result

    except Exception as e:
        logger.error(f"Time travel test failed: {e}")
        raise
    finally:
        spark.stop()


def generate_compliance_reports(**context):
    """Generate HIPAA compliance reports via Delta history audit trail"""
    from backend.delta_lake_integration import get_delta_manager

    spark = _create_spark("DeltaComplianceReports")

    try:
        delta_manager = get_delta_manager(spark)

        tables = [
            "uc_healthcare_prod.healthcare_db.lab_results",
            "uc_healthcare_prod.healthcare_db.patients",
            "uc_healthcare_prod.healthcare_db.providers",
            "uc_healthcare_prod.healthcare_db.claims",
        ]

        compliance_reports = {}
        for table in tables:
            try:
                report = delta_manager.get_compliance_report(table)
                compliance_reports[table] = report
            except Exception as e:
                logger.warning(f"Failed to generate compliance report for {table}: {e}")
                compliance_reports[table] = {"error": str(e)}

        logger.info(f"Generated {len(compliance_reports)} compliance reports")
        return compliance_reports

    except Exception as e:
        logger.error(f"Failed to generate compliance reports: {e}")
        raise
    finally:
        spark.stop()


def optimize_delta_tables(**context):
    """Optimize Delta tables: compaction + vacuum for Liquid Clustering"""
    from backend.delta_lake_integration import get_delta_manager

    spark = _create_spark("DeltaOptimization")

    try:
        delta_manager = get_delta_manager(spark)

        tables = [
            "uc_healthcare_prod.healthcare_db.lab_results",
            "uc_healthcare_prod.healthcare_db.patients",
            "uc_healthcare_prod.healthcare_db.providers",
            "uc_healthcare_prod.healthcare_db.claims",
        ]

        optimization_results = {}
        for table in tables:
            try:
                result = delta_manager.optimize_table_performance(table)
                optimization_results[table] = result
            except Exception as e:
                logger.warning(f"Failed to optimize {table}: {e}")
                optimization_results[table] = {"error": str(e)}

        logger.info(f"Optimized {len(optimization_results)} Delta tables")
        return optimization_results

    except Exception as e:
        logger.error(f"Failed to optimize Delta tables: {e}")
        raise
    finally:
        spark.stop()


# Spark job for Delta operations
spark_delta_job = SparkSubmitOperator(
    task_id='spark_delta_operations',
    application=os.path.join(SPARK_JOBS_DIR, 'delta_healthcare_operations.py'),
    conn_id='spark_default',
    driver_memory='6g',
    executor_memory='4g',
    executor_cores='2',
    num_executors='4',
    packages=[
        'io.delta:delta-spark_2.12:3.1.0',
        'org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0',
        'org.postgresql:postgresql:42.7.3',
    ],
    dag=dag,
)

# Task definitions
create_lab_results_task = PythonOperator(
    task_id='create_delta_lab_results',
    python_callable=create_delta_lab_results,
    dag=dag,
)

evolve_lab_schema_task = PythonOperator(
    task_id='evolve_lab_results_schema',
    python_callable=evolve_lab_results_schema,
    dag=dag,
)

create_patient_dim_task = PythonOperator(
    task_id='create_delta_patient_dimension',
    python_callable=create_delta_patient_dimension,
    dag=dag,
)

time_travel_test_task = PythonOperator(
    task_id='test_time_travel_queries',
    python_callable=test_time_travel_queries,
    dag=dag,
)

compliance_reports_task = PythonOperator(
    task_id='generate_compliance_reports',
    python_callable=generate_compliance_reports,
    dag=dag,
)

optimize_tables_task = PythonOperator(
    task_id='optimize_delta_tables',
    python_callable=optimize_delta_tables,
    dag=dag,
)

# Task dependencies
[create_lab_results_task, create_patient_dim_task] >> evolve_lab_schema_task
evolve_lab_schema_task >> time_travel_test_task
time_travel_test_task >> compliance_reports_task
compliance_reports_task >> optimize_tables_task
spark_delta_job >> optimize_tables_task
