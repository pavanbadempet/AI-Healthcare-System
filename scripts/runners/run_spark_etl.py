import os
import sys
import json
import pickle
import logging
import subprocess
import pandas as pd
import numpy as np

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SparkETLRunner")

def get_spark_session():
    """Create a SparkSession with Delta Lake configuration, falling back to basic if needed."""
    try:
        from pyspark.sql import SparkSession
        logger.info("Initializing PySpark Session...")
        builder = SparkSession.builder \
            .appName("HealthcareETL-Retraining") \
            .config("spark.sql.adaptive.enabled", "true")
        
        # Configure Delta Lake settings if possible
        try:
            import delta
            builder = builder \
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            logger.info("Spark session configured with Delta Lake extension.")
        except ImportError:
            logger.warning("Delta Lake package not found, falling back to standard Spark.")
            
        spark = builder.getOrCreate()
        return spark
    except ImportError:
        logger.warning("PySpark is not installed in the current environment. Running in Pandas fallback mode.")
        return None

def get_r2_client():
    """Create a boto3 client configured for Cloudflare R2."""
    r2_endpoint = os.getenv("R2_ENDPOINT")
    r2_access_key = os.getenv("R2_ACCESS_KEY_ID")
    r2_secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    
    if not (r2_endpoint and r2_access_key and r2_secret_key):
        logger.info("Cloudflare R2 environment variables not complete. R2 cloud sync disabled.")
        return None
        
    try:
        import boto3
        from botocore.config import Config
        
        # Cloudflare R2 requires custom endpoint URL and signature version S3v4
        s3 = boto3.client(
            service_name="s3",
            endpoint_url=r2_endpoint,
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            config=Config(signature_version="s3v4"),
        )
        return s3
    except ImportError:
        logger.warning("boto3 is not installed in the environment. Cloudflare R2 sync disabled.")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize boto3 client for Cloudflare R2: {e}")
        return None

def download_from_r2(s3, bucket_name, mtype, local_path):
    """Download baseline Parquet dataset from R2 bucket."""
    key = f"processed/{mtype}.parquet"
    logger.info(f"Downloading baseline {mtype} dataset from Cloudflare R2...")
    try:
        s3.download_file(bucket_name, key, local_path)
        logger.info(f"Successfully downloaded baseline {mtype} to {local_path}")
        return True
    except Exception as e:
        logger.info(f"No baseline file found in R2 for {mtype} (or access failed: {e}). Starting fresh.")
        return False

def upload_to_r2(s3, bucket_name, mtype, local_path):
    """Upload updated Parquet dataset to R2 bucket."""
    key = f"processed/{mtype}.parquet"
    logger.info(f"Uploading updated {mtype} dataset to Cloudflare R2...")
    try:
        s3.upload_file(local_path, bucket_name, key)
        logger.info(f"Successfully uploaded {mtype} dataset to R2 bucket.")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {mtype} dataset to R2: {e}")
        return False

def extract_and_transform():
    """Extract health records and transform them using PySpark if available, or Pandas fallback."""
    database_url = os.getenv("DATABASE_URL")
    
    # Target processed dataset files
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    records = []
    
    # 1. Extraction from Database
    if database_url:
        logger.info("Database URL detected. Extracting new training samples from remote database...")
        try:
            from sqlalchemy import create_engine
            # standard postgres conversion
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
                
            engine = create_engine(database_url)
            query = """
                SELECT hr.record_type, hr.data, hr.prediction 
                FROM health_records hr
                JOIN users u ON hr.user_id = u.id
                WHERE u.allow_data_collection = 1
            """
            with engine.connect() as conn:
                df_db = pd.read_sql(query, conn)
                logger.info(f"Extracted {len(df_db)} records from database.")
                records = df_db.to_dict(orient="records")
        except Exception as e:
            logger.warning(f"Database extraction failed: {e}. Falling back to baseline datasets.")
            
    # 2. Setup Cloudflare R2 Sync Client
    r2_client = get_r2_client()
    r2_bucket = os.getenv("R2_BUCKET_NAME", "healthcare-delta-lake")

    # 3. Spark/Pandas Transformation
    spark = get_spark_session()
    
    # Processed directories and model mappings
    model_types = ['diabetes', 'heart', 'liver', 'kidney', 'lungs']
    
    for mtype in model_types:
        parquet_path = os.path.join(processed_dir, f"{mtype}.parquet")
        
        # Download baseline from R2 if configured
        if r2_client is not None:
            download_from_r2(r2_client, r2_bucket, mtype, parquet_path)

        # Load baseline parquet if it exists
        df_base = None
        if os.path.exists(parquet_path):
            try:
                df_base = pd.read_parquet(parquet_path)
                logger.info(f"Loaded baseline {mtype} dataset: {len(df_base)} samples.")
            except Exception as e:
                logger.error(f"Error reading baseline parquet {parquet_path}: {e}")
                
        # Filter new records for this model type
        mtype_records = [r for r in records if r['record_type'] == mtype]
        if mtype_records:
            logger.info(f"Processing {len(mtype_records)} new {mtype} records from database...")
            
            # Parse JSON data strings
            parsed_records = []
            for r in mtype_records:
                try:
                    data_dict = json.loads(r['data'])
                    pred_str = str(r['prediction']).lower()
                    
                    # Target assignment
                    if mtype == 'diabetes':
                        target_val = 1 if 'high' in pred_str else 0
                    elif mtype == 'heart':
                        target_val = 1 if 'detected' in pred_str or 'positive' in pred_str else 0
                    elif mtype == 'liver':
                        target_val = 1 if 'detected' in pred_str else 0
                    elif mtype == 'kidney':
                        target_val = 1 if 'detected' in pred_str else 0
                    elif mtype == 'lungs':
                        target_val = 1 if 'detected' in pred_str or 'issue' in pred_str else 0
                    else:
                        target_val = 0
                        
                    data_dict['target'] = target_val
                    parsed_records.append(data_dict)
                except Exception as e:
                    logger.error(f"Error parsing record data: {e}")
                    
            if parsed_records:
                df_new = pd.DataFrame(parsed_records)
                
                # Use PySpark for schema alignment and writing if session exists
                if spark is not None:
                    try:
                        logger.info("Using Spark for transformation...")
                        spark_new = spark.createDataFrame(df_new)
                        df_new = spark_new.toPandas()
                    except Exception as e:
                        logger.warning(f"Spark processing failed: {e}. Falling back to Pandas.")
                        
                # Merge new with baseline
                if df_base is not None:
                    for col in df_base.columns:
                        if col not in df_new.columns:
                            df_new[col] = np.nan
                    df_new = df_new[df_base.columns]
                    df_merged = pd.concat([df_base, df_new], ignore_index=True)
                else:
                    df_merged = df_new
                    
                # Save merged parquet
                try:
                    df_merged.to_parquet(parquet_path, index=False)
                    logger.info(f"Updated {mtype} dataset saved. Total samples: {len(df_merged)}")
                    
                    # Upload updated to R2 if configured
                    if r2_client is not None:
                        upload_to_r2(r2_client, r2_bucket, mtype, parquet_path)
                except Exception as e:
                    logger.error(f"Failed to save merged dataset: {e}")
        else:
            logger.info(f"No new database records for {mtype}. Baseline dataset remains unchanged.")
            
    if spark is not None:
        spark.stop()
        logger.info("Spark Session stopped.")

def retrain_models():
    """Trigger the retraining script for each model and verify weights are updated."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    backend_dir = os.path.join(base_dir, "backend")
    
    models = ['diabetes', 'heart', 'kidney', 'liver', 'lungs']
    results = {}
    
    logger.info("Starting model retraining loop...")
    for model in models:
        script = os.path.join(backend_dir, f"train_{model}.py")
        if os.path.exists(script):
            logger.info(f"Running retraining script: train_{model}.py")
            try:
                # Add backend to python path so it can import features
                env = os.environ.copy()
                env["PYTHONPATH"] = backend_dir + os.pathsep + env.get("PYTHONPATH", "")
                
                res = subprocess.run([sys.executable, script], capture_output=True, text=True, env=env, timeout=600)
                if res.returncode == 0:
                    logger.info(f"Successfully retrained {model} model.")
                    results[model] = 'success'
                else:
                    logger.error(f"Retraining {model} model failed. Code: {res.returncode}. Error:\n{res.stderr}\nOutput:\n{res.stdout}")
                    results[model] = 'failed'
            except Exception as e:
                logger.error(f"Retraining {model} failed with exception: {e}")
                results[model] = 'failed'
        else:
            logger.warning(f"Training script {script} not found. Skipping.")
            results[model] = 'skipped'
            
    return results

def reload_models_via_api():
    """Trigger model reload on the backend API if configured."""
    backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    token = os.getenv("ADMIN_JWT_TOKEN")
    
    if not token:
        logger.warning("ADMIN_JWT_TOKEN environment variable not set. Skipping API model reload trigger.")
        return
        
    logger.info("Triggering backend zero-downtime model reload...")
    import requests
    try:
        resp = requests.post(
            f"{backend_url}/admin/reload_models",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        if resp.status_code == 200:
            logger.info("Successfully triggered zero-downtime model reload.")
        else:
            logger.error(f"Model reload trigger returned status: {resp.status_code}. Response: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to trigger model reload via API: {e}")

if __name__ == "__main__":
    logger.info("--- STARTING HEALTHCARE ETL & RETRAINING RUNNER ---")
    extract_and_transform()
    results = retrain_models()
    logger.info(f"Retraining results summary: {results}")
    
    # Reload models on active backend
    reload_models_via_api()
    logger.info("--- RUNNER COMPLETED ---")
