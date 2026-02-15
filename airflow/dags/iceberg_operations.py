"""
Airflow DAG for Apache Iceberg Operations
Schema evolution, time travel, and healthcare-specific operations
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago
import json
import logging

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
    'iceberg_healthcare_operations',
    default_args=default_args,
    description='Apache Iceberg operations for healthcare data',
    schedule_interval='@daily',
    catchup=False,
    tags=['healthcare', 'iceberg', 'schema-evolution', 'time-travel'],
)

def create_iceberg_lab_results(**context):
    """Create Iceberg table for lab results with healthcare optimizations"""
    from backend.iceberg_integration import get_iceberg_manager
    from pyspark.sql import SparkSession, types as T
    
    spark = SparkSession.builder \
        .appName("IcebergLabResults") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.healthcare_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.healthcare_catalog.type", "hive") \
        .config("spark.sql.catalog.healthcare_catalog.warehouse", "s3://healthcare-iceberg-warehouse/") \
        .getOrCreate()
    
    try:
        # Sample lab results data
        lab_data = [
            ("R001", "P001", "GLU", "Glucose", 95.5, "mg/dL", "70-100", "N", "2023-01-15 10:30:00", "LabTech1", "F001"),
            ("R002", "P001", "HBA1C", "Hemoglobin A1c", 6.2, "%", "4.0-5.6", "A", "2023-01-15 10:35:00", "LabTech1", "F001"),
            ("R003", "P002", "CHOL", "Cholesterol", 210.0, "mg/dL", "<200", "H", "2023-01-16 09:15:00", "LabTech2", "F001"),
            ("R004", "P003", "BP", "Blood Pressure", 120.0, "mmHg", "90-120", "N", "2023-01-17 14:20:00", "LabTech3", "F002"),
            ("R005", "P002", "TSH", "TSH", 2.1, "mIU/L", "0.4-4.0", "N", "2023-01-18 11:45:00", "LabTech1", "F001")
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
            T.StructField("facility_id", T.StringType(), True)
        ])
        
        # Create DataFrame
        lab_df = spark.createDataFrame(lab_data, lab_schema)
        
        # Convert date string to timestamp
        from pyspark.sql.functions import to_timestamp
        lab_df = lab_df.withColumn("test_date", to_timestamp(col("test_date"), "yyyy-MM-dd HH:mm:ss")) \
                       .withColumn("created_at", current_timestamp())
        
        # Initialize Iceberg manager
        iceberg_manager = get_iceberg_manager(spark)
        
        # Create lab results table
        result = iceberg_manager.create_lab_results_table(lab_df)
        
        logger.info(f"Created Iceberg lab results table: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to create Iceberg lab results table: {e}")
        raise
    finally:
        spark.stop()

def evolve_lab_results_schema(**context):
    """Evolve lab results schema for new test codes"""
    from backend.iceberg_integration import get_iceberg_manager
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder \
        .appName("IcebergSchemaEvolution") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.healthcare_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.healthcare_catalog.type", "hive") \
        .config("spark.sql.catalog.healthcare_catalog.warehouse", "s3://healthcare-iceberg-warehouse/") \
        .getOrCreate()
    
    try:
        # Simulate new lab codes being added
        new_lab_codes = ["VITD", "IRON", "CALCIUM", "PROTEIN"]
        
        # Initialize Iceberg manager
        iceberg_manager = get_iceberg_manager(spark)
        
        # Evolve schema
        result = iceberg_manager.evolve_lab_results_schema(new_lab_codes)
        
        logger.info(f"Evolved lab results schema: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to evolve lab results schema: {e}")
        raise
    finally:
        spark.stop()

def create_iceberg_patient_dimension(**context):
    """Create patient dimension with HIPAA compliance features"""
    from backend.iceberg_integration import get_iceberg_manager
    from pyspark.sql import SparkSession, types as T
    
    spark = SparkSession.builder \
        .appName("IcebergPatientDimension") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.healthcare_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.healthcare_catalog.type", "hive") \
        .config("spark.sql.catalog.healthcare_catalog.warehouse", "s3://healthcare-iceberg-warehouse/") \
        .getOrCreate()
    
    try:
        # Sample patient data
        patient_data = [
            ("P001", "John", "Doe", "1980-01-15", "M", "john.doe@email.com", "555-1234", "123 Main St", "A123", "Dr. Smith"),
            ("P002", "Jane", "Smith", "1975-05-22", "F", "jane.smith@email.com", "555-5678", "456 Oak Ave", "B456", "Dr. Johnson"),
            ("P003", "Bob", "Wilson", "1990-12-10", "M", "bob.wilson@email.com", "555-9012", "789 Pine Rd", "C789", "Dr. Brown")
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
            T.StructField("primary_care_physician", T.StringType(), True)
        ])
        
        # Create DataFrame
        patient_df = spark.createDataFrame(patient_data, patient_schema)
        
        # Add audit columns
        from pyspark.sql.functions import col, lit, current_timestamp, to_date
        patient_df = patient_df.withColumn("created_at", current_timestamp()) \
                             .withColumn("updated_at", current_timestamp()) \
                             .withColumn("updated_date", to_date(col("updated_at")))
        
        # Initialize Iceberg manager
        iceberg_manager = get_iceberg_manager(spark)
        
        # Create patient dimension
        result = iceberg_manager.create_patient_dimension(patient_df)
        
        logger.info(f"Created Iceberg patient dimension: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to create Iceberg patient dimension: {e}")
        raise
    finally:
        spark.stop()

def evolve_patient_schema_hipaa(**context):
    """Evolve patient schema for HIPAA compliance"""
    from backend.iceberg_integration import get_iceberg_manager
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder \
        .appName("IcebergHIPAAEvolution") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.healthcare_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.healthcare_catalog.type", "hive") \
        .config("spark.sql.catalog.healthcare_catalog.warehouse", "s3://healthcare-iceberg-warehouse/") \
        .getOrCreate()
    
    try:
        # Initialize Iceberg manager
        iceberg_manager = get_iceberg_manager(spark)
        
        # Evolve schema for HIPAA compliance
        result = iceberg_manager.evolve_patient_schema_for_hipaa()
        
        logger.info(f"Evolved patient schema for HIPAA: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to evolve patient schema for HIPAA: {e}")
        raise
    finally:
        spark.stop()

def test_time_travel_queries(**context):
    """Test Iceberg time travel capabilities"""
    from backend.iceberg_integration import get_iceberg_manager
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder \
        .appName("IcebergTimeTravel") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.healthcare_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.healthcare_catalog.type", "hive") \
        .config("spark.sql.catalog.healthcare_catalog.warehouse", "s3://healthcare-iceberg-warehouse/") \
        .getOrCreate()
    
    try:
        # Initialize Iceberg manager
        iceberg_manager = get_iceberg_manager(spark)
        
        # Get table history
        table_name = "healthcare_catalog.healthcare_db.lab_results"
        history = iceberg_manager.schema_manager.get_table_history(table_name)
        
        # Get snapshots
        snapshots = iceberg_manager.schema_manager.get_table_snapshots(table_name)
        
        # Test time travel if snapshots exist
        time_travel_results = []
        if snapshots:
            latest_snapshot = snapshots[-1]['snapshot_id']
            
            # Query at snapshot
            historical_df = iceberg_manager.schema_manager.query_at_snapshot(
                table_name, latest_snapshot
            )
            
            time_travel_results.append({
                'snapshot_id': latest_snapshot,
                'record_count': historical_df.count(),
                'query_time': 'historical'
            })
        
        result = {
            'table_name': table_name,
            'history_count': len(history),
            'snapshot_count': len(snapshots),
            'time_travel_results': time_travel_results,
            'time_travel_enabled': len(snapshots) > 0
        }
        
        logger.info(f"Time travel test results: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Time travel test failed: {e}")
        raise
    finally:
        spark.stop()

def generate_compliance_reports(**context):
    """Generate compliance reports for healthcare tables"""
    from backend.iceberg_integration import get_iceberg_manager
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder \
        .appName("IcebergComplianceReports") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.healthcare_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.healthcare_catalog.type", "hive") \
        .config("spark.sql.catalog.healthcare_catalog.warehouse", "s3://healthcare-iceberg-warehouse/") \
        .getOrCreate()
    
    try:
        # Initialize Iceberg manager
        iceberg_manager = get_iceberg_manager(spark)
        
        # Generate compliance reports for all tables
        tables = [
            "healthcare_catalog.healthcare_db.lab_results",
            "healthcare_catalog.healthcare_db.patients",
            "healthcare_catalog.healthcare_db.providers",
            "healthcare_catalog.healthcare_db.claims"
        ]
        
        compliance_reports = {}
        
        for table in tables:
            try:
                report = iceberg_manager.get_compliance_report(table)
                compliance_reports[table] = report
            except Exception as e:
                logger.warning(f"Failed to generate compliance report for {table}: {e}")
                compliance_reports[table] = {'error': str(e)}
        
        logger.info(f"Generated {len(compliance_reports)} compliance reports")
        return compliance_reports
        
    except Exception as e:
        logger.error(f"Failed to generate compliance reports: {e}")
        raise
    finally:
        spark.stop()

def optimize_iceberg_tables(**context):
    """Optimize Iceberg tables for better performance"""
    from backend.iceberg_integration import get_iceberg_manager
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder \
        .appName("IcebergOptimization") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.healthcare_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.healthcare_catalog.type", "hive") \
        .config("spark.sql.catalog.healthcare_catalog.warehouse", "s3://healthcare-iceberg-warehouse/") \
        .getOrCreate()
    
    try:
        # Initialize Iceberg manager
        iceberg_manager = get_iceberg_manager(spark)
        
        # Optimize all tables
        tables = [
            "healthcare_catalog.healthcare_db.lab_results",
            "healthcare_catalog.healthcare_db.patients",
            "healthcare_catalog.healthcare_db.providers",
            "healthcare_catalog.healthcare_db.claims"
        ]
        
        optimization_results = {}
        
        for table in tables:
            try:
                result = iceberg_manager.optimize_table_performance(table)
                optimization_results[table] = result
            except Exception as e:
                logger.warning(f"Failed to optimize {table}: {e}")
                optimization_results[table] = {'error': str(e)}
        
        logger.info(f"Optimized {len(optimization_results)} Iceberg tables")
        return optimization_results
        
    except Exception as e:
        logger.error(f"Failed to optimize Iceberg tables: {e}")
        raise
    finally:
        spark.stop()

# Spark job for Iceberg operations
spark_iceberg_job = SparkSubmitOperator(
    task_id='spark_iceberg_operations',
    application='/opt/airflow/spark_jobs/iceberg_healthcare_operations.py',
    conn_id='spark_default',
    driver_memory='6g',
    executor_memory='4g',
    executor_cores='2',
    num_executors='4',
    packages=[
        'org.apache.iceberg:iceberg-spark-runtime:1.4.2',
        'org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0',
        'org.postgresql:postgresql:42.2.18'
    ],
    dag=dag,
)

# Task definitions
create_lab_results_task = PythonOperator(
    task_id='create_iceberg_lab_results',
    python_callable=create_iceberg_lab_results,
    dag=dag,
)

evolve_lab_schema_task = PythonOperator(
    task_id='evolve_lab_results_schema',
    python_callable=evolve_lab_results_schema,
    dag=dag,
)

create_patient_dim_task = PythonOperator(
    task_id='create_iceberg_patient_dimension',
    python_callable=create_iceberg_patient_dimension,
    dag=dag,
)

evolve_hipaa_schema_task = PythonOperator(
    task_id='evolve_patient_schema_hipaa',
    python_callable=evolve_patient_schema_hipaa,
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
    task_id='optimize_iceberg_tables',
    python_callable=optimize_iceberg_tables,
    dag=dag,
)

# Task dependencies
[create_lab_results_task, create_patient_dim_task] >> evolve_lab_schema_task
evolve_lab_schema_task >> evolve_hipaa_schema_task
evolve_hipaa_schema_task >> time_travel_test_task
time_travel_test_task >> compliance_reports_task
compliance_reports_task >> optimize_tables_task
spark_iceberg_job >> optimize_tables_task
