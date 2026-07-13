"""
Airflow DAG for Advanced Healthcare Data Modeling
Delta Lake, SCD Patterns, Schema Evolution, Time Travel
"""

import logging
import os
from datetime import datetime, timedelta

# Environment-configurable paths to support multiple deployment environments
WAREHOUSE_PATH = os.getenv("LAKEHOUSE_PATH", "/tmp/healthcare_warehouse")
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

# DAG definition
dag = DAG(
    'healthcare_data_modeling',
    default_args=default_args,
    description='Advanced Data Modeling with Delta Lake, SCD Patterns, and Time Travel',
    schedule_interval='@daily',
    catchup=False,
    tags=['healthcare', 'data-modeling', 'delta-lake', 'scd', 'time-travel'],
)

def create_patient_dimension_scd2(**context):
    """Create patient dimension with SCD Type 2 using Delta Lake"""
    from pyspark.sql.types import StringType, StructField, StructType

    from backend.advanced_data_modeling import create_spark_session_with_lakehouse, get_data_modeler

    # Create Spark session with lakehouse support
    spark = create_spark_session_with_lakehouse()

    try:
        # Sample patient data (in real scenario, this would come from source systems)
        patient_data = [
            ("P001", "John", "Doe", "1980-01-15", "M", "john.doe@email.com", "555-1234", "123 Main St", "A123", "Dr. Smith"),
            ("P002", "Jane", "Smith", "1975-05-22", "F", "jane.smith@email.com", "555-5678", "456 Oak Ave", "B456", "Dr. Johnson"),
            ("P003", "Bob", "Wilson", "1990-12-10", "M", "bob.wilson@email.com", "555-9012", "789 Pine Rd", "C789", "Dr. Brown")
        ]

        patient_schema = StructType([
            StructField("patient_id", StringType(), False),
            StructField("first_name", StringType(), True),
            StructField("last_name", StringType(), True),
            StructField("date_of_birth", StringType(), True),
            StructField("gender", StringType(), True),
            StructField("email", StringType(), True),
            StructField("phone", StringType(), True),
            StructField("address", StringType(), True),
            StructField("insurance_id", StringType(), True),
            StructField("primary_care_physician", StringType(), True)
        ])

        # Create DataFrame
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.appName("PatientDimension").getOrCreate()
        patient_df = spark.createDataFrame(patient_data, patient_schema)

        # Add audit columns
        from pyspark.sql.functions import current_timestamp
        patient_df = patient_df.withColumn("created_at", current_timestamp()) \
                             .withColumn("updated_at", current_timestamp())

        # Initialize data modeler
        data_modeler = get_data_modeler(spark, WAREHOUSE_PATH)

        # Create patient dimension with SCD Type 2
        result = data_modeler.create_patient_dimension(patient_df)

        logger.info(f"Patient dimension created: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to create patient dimension: {e}")
        raise
    finally:
        spark.stop()

def create_lab_results_fact_delta(**context):
    """Create lab results fact table using Delta Lake"""
    from pyspark.sql.types import FloatType, StringType, StructField, StructType

    from backend.advanced_data_modeling import create_spark_session_with_lakehouse, get_data_modeler

    spark = create_spark_session_with_lakehouse()

    try:
        # Sample lab results data
        lab_data = [
            ("R001", "P001", "GLU", "Glucose", 95.5, "mg/dL", "70-100", "N", "2023-01-15 10:30:00", "LabTech1", "F001"),
            ("R002", "P001", "HBA1C", "Hemoglobin A1c", 6.2, "%", "4.0-5.6", "A", "2023-01-15 10:35:00", "LabTech1", "F001"),
            ("R003", "P002", "CHOL", "Cholesterol", 210.0, "mg/dL", "<200", "H", "2023-01-16 09:15:00", "LabTech2", "F001"),
            ("R004", "P003", "BP", "Blood Pressure", 120.0, "mmHg", "90-120", "N", "2023-01-17 14:20:00", "LabTech3", "F002")
        ]

        lab_schema = StructType([
            StructField("result_id", StringType(), False),
            StructField("patient_id", StringType(), False),
            StructField("test_code", StringType(), False),
            StructField("test_name", StringType(), True),
            StructField("result_value", FloatType(), True),
            StructField("result_unit", StringType(), True),
            StructField("reference_range", StringType(), True),
            StructField("abnormal_flag", StringType(), True),
            StructField("test_date", StringType(), True),
            StructField("performed_by", StringType(), True),
            StructField("facility_id", StringType(), True)
        ])

        # Create DataFrame
        lab_df = spark.createDataFrame(lab_data, lab_schema)

        # Add audit columns
        from pyspark.sql.functions import col, current_timestamp, to_timestamp
        lab_df = lab_df.withColumn("test_date", to_timestamp(col("test_date"), "yyyy-MM-dd HH:mm:ss")) \
                      .withColumn("created_at", current_timestamp())

        # Initialize data modeler
        data_modeler = get_data_modeler(spark, WAREHOUSE_PATH)

        # Create lab results fact with Delta Lake
        result = data_modeler.create_lab_results_fact(lab_df)

        logger.info(f"Lab results fact created: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to create lab results fact: {e}")
        raise
    finally:
        spark.stop()

def apply_schema_evolution_demo(**context):
    """Demonstrate schema evolution capabilities"""
    from backend.advanced_data_modeling import create_spark_session_with_lakehouse, get_data_modeler

    spark = create_spark_session_with_lakehouse()

    try:
        # Initialize data modeler
        data_modeler = get_data_modeler(spark, WAREHOUSE_PATH)

        # Apply schema evolution example
        result = data_modeler.apply_schema_evolution_example()

        logger.info(f"Schema evolution applied: {result}")
        return result

    except Exception as e:
        logger.error(f"Schema evolution failed: {e}")
        raise
    finally:
        spark.stop()

def create_claims_dimension_scd2(**context):
    """Create claims dimension with SCD Type 2"""
    from pyspark.sql.types import FloatType, StringType, StructField, StructType

    from backend.advanced_data_modeling import create_spark_session_with_lakehouse

    spark = create_spark_session_with_lakehouse()

    try:
        # Sample claims data
        claims_data = [
            ("CLM001", "P001", "PROV001", "2023-01-15", "99213", "Z00.00", 150.00, 120.00, 100.00, "PAID"),
            ("CLM002", "P002", "PROV002", "2023-01-16", "99214", "J45.909", 200.00, 180.00, 150.00, "PAID"),
            ("CLM003", "P003", "PROV001", "2023-01-17", "80053", "R50.9", 75.00, 70.00, 65.00, "PENDING")
        ]

        claims_schema = StructType([
            StructField("claim_id", StringType(), False),
            StructField("patient_id", StringType(), False),
            StructField("provider_id", StringType(), False),
            StructField("service_date", StringType(), False),
            StructField("procedure_code", StringType(), False),
            StructField("diagnosis_code", StringType(), True),
            StructField("billed_amount", FloatType(), False),
            StructField("allowed_amount", FloatType(), True),
            StructField("paid_amount", FloatType(), True),
            StructField("claim_status", StringType(), False)
        ])

        # Create DataFrame
        claims_df = spark.createDataFrame(claims_data, claims_schema)

        # Add audit columns
        from pyspark.sql.functions import col, current_timestamp, lit, to_date
        claims_df = claims_df.withColumn("service_date", to_date(col("service_date"))) \
                           .withColumn("created_at", current_timestamp()) \
                           .withColumn("updated_at", current_timestamp())

        # Create claims table with SCD Type 2
        table_path = os.path.join(WAREHOUSE_PATH, "claims")
        from backend.advanced_data_modeling import DataModelConfig, DeltaLakeManager, SCDType, TableFormat

        delta_manager = DeltaLakeManager(spark, table_path)
        config = DataModelConfig(
            table_name='claims',
            table_format=TableFormat.DELTA,
            scd_type=SCDType.TYPE2,
            cluster_columns=['service_date', 'claim_id', 'patient_id'],
            business_keys=['claim_id'],
            tracking_columns=['claim_status', 'paid_amount'],
            enable_cdc=True
        )

        if not spark.catalog._existsTable("claims"):
            # Create new table
            claims_with_audit = claims_df.withColumn("updated_date", col("updated_at").cast("date")) \
                                       .withColumn("is_current", lit(True)) \
                                       .withColumn("effective_date", current_timestamp()) \
                                       .withColumn("end_date", lit(None))

            delta_manager.create_delta_table(claims_with_audit, config)
        else:
            # Apply SCD Type 2
            result = delta_manager.upsert_to_delta(claims_df, config, None)

        result = {
            'status': 'success',
            'table': 'claims',
            'scd_type': 2,
            'records_processed': claims_df.count()
        }

        logger.info(f"Claims dimension created: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to create claims dimension: {e}")
        raise
    finally:
        spark.stop()

def time_travel_query_demo(**context):
    """Demonstrate Delta Lake time travel capabilities"""
    from delta.tables import DeltaTable

    from backend.advanced_data_modeling import create_spark_session_with_lakehouse

    spark = create_spark_session_with_lakehouse()

    try:
        # Query historical data
        table_path = os.path.join(WAREHOUSE_PATH, "patients")

        if spark.catalog._existsTable("patients"):
            # Get current version
            delta_table = DeltaTable.forPath(spark, table_path)
            current_version = delta_table.history().limit(1).collect()[0]['version']

            # Query previous version if available
            if current_version > 0:
                historical_df = spark.read.format("delta") \
                    .option("versionAsOf", current_version - 1) \
                    .load(table_path)

                historical_count = historical_df.count()

                result = {
                    'current_version': current_version,
                    'queried_version': current_version - 1,
                    'historical_records': historical_count,
                    'time_travel_enabled': True
                }
            else:
                result = {
                    'current_version': current_version,
                    'time_travel_enabled': True,
                    'message': 'No previous versions available'
                }
        else:
            result = {'time_travel_enabled': False, 'message': 'Table does not exist'}

        logger.info(f"Time travel query result: {result}")
        return result

    except Exception as e:
        logger.error(f"Time travel query failed: {e}")
        raise
    finally:
        spark.stop()

def get_data_lineage_report(**context):
    """Generate comprehensive data lineage report"""
    from backend.advanced_data_modeling import create_spark_session_with_lakehouse, get_data_modeler

    spark = create_spark_session_with_lakehouse()

    try:
        # Initialize data modeler
        data_modeler = get_data_modeler(spark, WAREHOUSE_PATH)

        # Generate lineage report
        lineage_report = data_modeler.get_data_lineage_report()

        logger.info(f"Data lineage report generated with {len(lineage_report['tables'])} tables")
        return lineage_report

    except Exception as e:
        logger.error(f"Failed to generate data lineage report: {e}")
        raise
    finally:
        spark.stop()

def optimize_delta_tables(**context):
    """Optimize Delta Lake tables for performance"""
    from backend.advanced_data_modeling import (
        DataModelConfig,
        DeltaLakeManager,
        SCDType,
        TableFormat,
        create_spark_session_with_lakehouse,
    )

    spark = create_spark_session_with_lakehouse()

    try:
        optimization_results = []

        # Optimize patient table
        patient_path = os.path.join(WAREHOUSE_PATH, "patients")
        if spark.catalog._existsTable("patients"):
            delta_manager = DeltaLakeManager(spark, patient_path)
            config = DataModelConfig(
                table_name='patients',
                table_format=TableFormat.DELTA,
                scd_type=SCDType.TYPE2,
                cluster_columns=['patient_id', 'updated_date'],
                enable_cdc=True
            )

            patient_opt = delta_manager.optimize_table(config)
            optimization_results.append(patient_opt)

        # Optimize claims table
        claims_path = os.path.join(WAREHOUSE_PATH, "claims")
        if spark.catalog._existsTable("claims"):
            delta_manager = DeltaLakeManager(spark, claims_path)
            config = DataModelConfig(
                table_name='claims',
                table_format=TableFormat.DELTA,
                scd_type=SCDType.TYPE2,
                cluster_columns=['service_date', 'claim_id'],
                enable_cdc=True
            )

            claims_opt = delta_manager.optimize_table(config)
            optimization_results.append(claims_opt)

        result = {
            'optimization_completed': True,
            'tables_optimized': len(optimization_results),
            'results': optimization_results
        }

        logger.info(f"Delta tables optimized: {result}")
        return result

    except Exception as e:
        logger.error(f"Delta table optimization failed: {e}")
        raise
    finally:
        spark.stop()

# Spark job for advanced data modeling
spark_modeling_task = SparkSubmitOperator(
    task_id='spark_advanced_modeling',
    application=os.path.join(SPARK_JOBS_DIR, 'healthcare_data_modeling.py'),
    conn_id='spark_default',
    driver_memory='6g',
    executor_memory='4g',
    executor_cores='2',
    num_executors='4',
    packages=[
        'io.delta:delta-spark_2.12:3.1.0',
        'org.postgresql:postgresql:42.7.3',
    ],
    dag=dag,
)

# Task definitions
create_patient_dim_task = PythonOperator(
    task_id='create_patient_dimension_scd2',
    python_callable=create_patient_dimension_scd2,
    dag=dag,
)

create_lab_results_fact_task = PythonOperator(
    task_id='create_lab_results_fact_delta',
    python_callable=create_lab_results_fact_delta,
    dag=dag,
)

create_claims_dim_task = PythonOperator(
    task_id='create_claims_dimension_scd2',
    python_callable=create_claims_dimension_scd2,
    dag=dag,
)

schema_evolution_task = PythonOperator(
    task_id='apply_schema_evolution_demo',
    python_callable=apply_schema_evolution_demo,
    dag=dag,
)

time_travel_task = PythonOperator(
    task_id='time_travel_query_demo',
    python_callable=time_travel_query_demo,
    dag=dag,
)

data_lineage_task = PythonOperator(
    task_id='get_data_lineage_report',
    python_callable=get_data_lineage_report,
    dag=dag,
)

optimize_tables_task = PythonOperator(
    task_id='optimize_delta_tables',
    python_callable=optimize_delta_tables,
    dag=dag,
)

# Task dependencies
[create_patient_dim_task, create_lab_results_fact_task, create_claims_dim_task] >> schema_evolution_task
schema_evolution_task >> time_travel_task
time_travel_task >> data_lineage_task
data_lineage_task >> optimize_tables_task
spark_modeling_task >> optimize_tables_task
