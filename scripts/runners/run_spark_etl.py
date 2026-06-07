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

def get_hf_client():
    """Create a Hugging Face HfApi client if token and dataset ID are configured."""
    hf_token = os.getenv("HF_TOKEN")
    dataset_id = os.getenv("HF_DATASET_ID")
    
    if not (hf_token and dataset_id):
        logger.info("HF_TOKEN or HF_DATASET_ID environment variables not set. HF private dataset sync disabled.")
        return None, None
        
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=hf_token)
        return api, dataset_id
    except ImportError:
        logger.warning("huggingface_hub is not installed. HF private dataset sync disabled.")
        return None, None
    except Exception as e:
        logger.error(f"Failed to initialize Hugging Face client: {e}")
        return None, None

def download_from_hf(api, dataset_id, mtype, local_dir, local_path):
    """Download baseline Parquet dataset from private HF Dataset."""
    filename = f"processed/{mtype}.parquet"
    logger.info(f"Downloading baseline {mtype} dataset from Hugging Face private dataset {dataset_id}...")
    try:
        # Download from private HF Dataset to local directory
        api.hf_hub_download(
            repo_id=dataset_id,
            repo_type="dataset",
            filename=filename,
            local_dir=local_dir,
            local_dir_use_symlinks=False
        )
        logger.info(f"Successfully downloaded baseline {mtype} from HF.")
        return True
    except Exception as e:
        logger.info(f"No baseline file found in HF Dataset for {mtype} (or access failed: {e}). Starting fresh.")
        return False

def upload_to_hf(api, dataset_id, mtype, local_path):
    """Upload updated Parquet dataset to private HF Dataset."""
    filename = f"processed/{mtype}.parquet"
    logger.info(f"Uploading updated {mtype} dataset to Hugging Face private dataset {dataset_id}...")
    try:
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=filename,
            repo_id=dataset_id,
            repo_type="dataset"
        )
        logger.info(f"Successfully uploaded {mtype} dataset to Hugging Face private dataset.")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {mtype} dataset to Hugging Face: {e}")
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
            
    # 2. Setup Hugging Face private dataset client
    hf_client, hf_dataset_id = get_hf_client()

    # 3. Spark/Pandas Transformation
    spark = get_spark_session()
    
    # Processed directories and model mappings
    model_types = ['diabetes', 'heart', 'liver', 'kidney', 'lungs']
    
    for mtype in model_types:
        parquet_path = os.path.join(processed_dir, f"{mtype}.parquet")
        
        # Download baseline from HF Dataset if configured
        if hf_client is not None:
            download_from_hf(hf_client, hf_dataset_id, mtype, base_dir, parquet_path)

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
                    
                    # Upload updated to HF Dataset if configured
                    if hf_client is not None:
                        upload_to_hf(hf_client, hf_dataset_id, mtype, parquet_path)
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
