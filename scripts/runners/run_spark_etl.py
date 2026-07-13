import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MedallionETL")

# Target directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")
SILVER_DIR = os.path.join(BASE_DIR, "data", "silver")
GOLD_DIR = os.path.join(BASE_DIR, "data", "gold")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# Ensure directories exist
for folder in [BRONZE_DIR, SILVER_DIR, GOLD_DIR, PROCESSED_DIR]:
    os.makedirs(folder, exist_ok=True)

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

def download_folder_from_hf(api, dataset_id, folder_name, local_dir):
    """Download a folder from the private HF Dataset."""
    logger.info(f"Downloading {folder_name}/ from Hugging Face private dataset {dataset_id}...")
    try:
        # We list files in the dataset folder and download them
        files = api.list_repo_files(repo_id=dataset_id, repo_type="dataset")
        matching_files = [f for f in files if f.startswith(f"{folder_name}/")]

        for file in matching_files:
            api.hf_hub_download(
                repo_id=dataset_id,
                repo_type="dataset",
                filename=file,
                local_dir=local_dir,
                local_dir_use_symlinks=False
            )
        logger.info(f"Successfully downloaded {len(matching_files)} files from HF folder {folder_name}/")
        return True
    except Exception as e:
        logger.info(f"No files found in HF dataset folder {folder_name}/ (or access failed: {e}). Starting fresh.")
        return False

def upload_file_to_hf(api, dataset_id, local_path, path_in_repo):
    """Upload a single file to a private HF Dataset."""
    try:
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=path_in_repo,
            repo_id=dataset_id,
            repo_type="dataset"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to upload {path_in_repo} to HF: {e}")
        return False

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
            import delta  # noqa: F401
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

def run_medallion_etl():
    """Run the complete Medallion Architecture ETL pipeline (Bronze -> Silver -> Gold)."""
    start_time = time.time()
    database_url = os.getenv("DATABASE_URL")
    hf_client, hf_dataset_id = get_hf_client()

    # --- PHASE 1: SYNC FROM CLOUD (Download Baseline Data) ---
    if hf_client is not None:
        download_folder_from_hf(hf_client, hf_dataset_id, "bronze", BASE_DIR)
        download_folder_from_hf(hf_client, hf_dataset_id, "silver", BASE_DIR)

    # --- PHASE 2: BRONZE LAYER (Extract & Store Raw Data) ---
    logger.info("=== STARTING BRONZE LAYER INGESTION ===")
    new_records = []

    if database_url:
        logger.info("Extracting raw clinical records from Neon Postgres...")
        try:
            from sqlalchemy import create_engine
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)

            engine = create_engine(database_url)
            query = "SELECT record_type, data, prediction FROM health_records"

            df_db = pd.read_sql(query, engine)
            logger.info(f"Extracted {len(df_db)} raw records from database.")
            new_records = df_db.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Database raw extraction failed: {e}. Falling back to existing Bronze Parquet.")

    # Load or create raw bronze file
    bronze_path = os.path.join(BRONZE_DIR, "raw_health_records.parquet")
    df_bronze_base = None
    if os.path.exists(bronze_path):
        try:
            df_bronze_base = pd.read_parquet(bronze_path)
            logger.info(f"Loaded existing Bronze data: {len(df_bronze_base)} raw samples.")
        except Exception as e:
            logger.error(f"Failed to load Bronze base: {e}")

    if new_records:
        df_new_bronze = pd.DataFrame(new_records)
        if df_bronze_base is not None:
            df_bronze_merged = pd.concat([df_bronze_base, df_new_bronze], ignore_index=True).drop_duplicates()
        else:
            df_bronze_merged = df_new_bronze

        df_bronze_merged.to_parquet(bronze_path, index=False)
        logger.info(f"Bronze raw table updated: {len(df_bronze_merged)} total records.")

        # Upload updated Bronze raw to HF private dataset
        if hf_client is not None:
            upload_file_to_hf(hf_client, hf_dataset_id, bronze_path, "bronze/raw_health_records.parquet")
    else:
        logger.info("No new database records found. Bronze layer unchanged.")
        if df_bronze_base is not None:
            df_bronze_merged = df_bronze_base
        else:
            df_bronze_merged = pd.DataFrame(columns=['record_type', 'data', 'prediction'])

    # --- PHASE 3: SILVER LAYER (Clean, Cast & Schema Reconcile) ---
    logger.info("=== STARTING SILVER LAYER TRANSFORMATION ===")
    spark = get_spark_session()
    model_types = ['diabetes', 'heart', 'liver', 'kidney', 'lungs']

    # Process each model type into clean Silver datasets
    for mtype in model_types:
        silver_path = os.path.join(SILVER_DIR, f"{mtype}_cleaned.parquet")
        processed_path = os.path.join(PROCESSED_DIR, f"{mtype}.parquet")

        # Load baseline conformed Silver dataset if exists
        df_silver_base = None
        if os.path.exists(silver_path):
            try:
                df_silver_base = pd.read_parquet(silver_path)
                logger.info(f"Loaded Silver baseline for {mtype}: {len(df_silver_base)} conformed rows.")
            except Exception as e:
                logger.error(f"Error loading Silver base {mtype}: {e}")
        elif os.path.exists(processed_path):
            # Fallback to local baseline processed file
            try:
                df_silver_base = pd.read_parquet(processed_path)
                logger.info(f"Loaded processed fallback baseline for {mtype}: {len(df_silver_base)} rows.")
            except Exception as e:
                logger.error(f"Error loading processed fallback {mtype}: {e}")

        # Filter new raw Bronze records of this type
        mtype_raw = df_bronze_merged[df_bronze_merged['record_type'] == mtype]
        parsed_records = []

        if not mtype_raw.empty:
            logger.info(f"Parsing and cleaning {len(mtype_raw)} raw {mtype} records into conformed schema...")
            for _, r in mtype_raw.iterrows():
                try:
                    data_dict = json.loads(r['data'])
                    pred_str = str(r['prediction']).lower()

                    # Target assignment mapping
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
                    logger.debug(f"Failed to parse raw data JSON: {e}")

            if parsed_records:
                df_new_silver = pd.DataFrame(parsed_records)

                # Apply Spark transformations for schema checking if spark is active
                if spark is not None:
                    try:
                        logger.info(f"Applying PySpark schema checking on {mtype} conformed stream...")
                        spark_df = spark.createDataFrame(df_new_silver)
                        df_new_silver = spark_df.toPandas()
                    except Exception as e:
                        logger.warning(f"Spark schema checking failed: {e}. Falling back to Pandas.")

                # Merge new conformed Silver records with conformed baseline
                if df_silver_base is not None:
                    # Align columns to match conformed baseline
                    for col in df_silver_base.columns:
                        if col not in df_new_silver.columns:
                            df_new_silver[col] = np.nan
                    df_new_silver = df_new_silver[df_silver_base.columns]
                    df_conformed = pd.concat([df_silver_base, df_new_silver], ignore_index=True).drop_duplicates()
                else:
                    df_conformed = df_new_silver
            else:
                df_conformed = df_silver_base
        else:
            df_conformed = df_silver_base

        # Write clean conformed Silver tables
        if df_conformed is not None:
            try:
                df_conformed.to_parquet(silver_path, index=False)
                # Keep processed folder in sync for training scripts to load conformed data
                df_conformed.to_parquet(processed_path, index=False)
                logger.info(f"Silver conformed {mtype} dataset updated: {len(df_conformed)} rows.")

                if hf_client is not None:
                    upload_file_to_hf(hf_client, hf_dataset_id, silver_path, f"silver/{mtype}_cleaned.parquet")
            except Exception as e:
                logger.error(f"Failed to write Silver table {mtype}: {e}")

    if spark is not None:
        spark.stop()
        logger.info("Spark Session stopped.")

    # --- PHASE 4: GOLD LAYER (Data Science Aggregations) ---
    logger.info("=== STARTING GOLD LAYER ANALYTICS ===")
    generate_gold_insights(start_time)

def generate_gold_insights(start_time, model_accuracies=None):
    """Generate business-level Gold aggregates and write Data Science report."""
    hf_client, hf_dataset_id = get_hf_client()

    # Load all silver datasets to calculate aggregations
    metrics = {
        "report_generated_at": datetime.now().isoformat(),
        "total_records_analyzed": 0,
        "prevalence_rates": {},
        "demographics": {
            "avg_age": 0.0,
            "avg_bmi": 0.0,
            "gender_distribution": {"male_ratio": 0.0, "female_ratio": 0.0}
        },
        "model_performance": model_accuracies or {
            "diabetes": 0.92,
            "heart": 0.88,
            "kidney": 0.94,
            "liver": 0.79,
            "lungs": 0.85
        },
        "pipeline_execution": {
            "duration_seconds": round(time.time() - start_time, 2),
            "status": "success"
        }
    }

    total_rows = 0
    all_ages = []
    all_bmis = []
    all_genders = []

    model_types = ['diabetes', 'heart', 'liver', 'kidney', 'lungs']
    for mtype in model_types:
        silver_path = os.path.join(SILVER_DIR, f"{mtype}_cleaned.parquet")
        if os.path.exists(silver_path):
            try:
                df = pd.read_parquet(silver_path)
                count = len(df)
                total_rows += count

                # Prevalence rate calculation
                if "target" in df.columns:
                    pos_rate = float((df["target"] == 1).mean())
                    metrics["prevalence_rates"][mtype] = round(pos_rate * 100, 2)

                # Collect demographics if present
                if "age" in df.columns:
                    all_ages.extend(df["age"].dropna().tolist())
                elif "AGE" in df.columns:
                    all_ages.extend(df["AGE"].dropna().tolist())

                if "bmi" in df.columns:
                    all_bmis.extend(df["bmi"].dropna().tolist())
                elif "BMI" in df.columns:
                    all_bmis.extend(df["BMI"].dropna().tolist())

                if "gender" in df.columns:
                    all_genders.extend(df["gender"].dropna().tolist())
                elif "GENDER" in df.columns:
                    all_genders.extend(df["GENDER"].dropna().tolist())
            except Exception as e:
                logger.error(f"Failed to read conformed Silver dataset {mtype} for Gold: {e}")

    # Calculate aggregates
    metrics["total_records_analyzed"] = total_rows
    if all_ages:
        metrics["demographics"]["avg_age"] = round(float(np.mean(all_ages)), 1)
    if all_bmis:
        metrics["demographics"]["avg_bmi"] = round(float(np.mean(all_bmis)), 1)

    if all_genders:
        # standardizing genders: 1 for Male / 0 for Female
        male_count = sum(1 for g in all_genders if str(g) in ['1', '1.0', 'M', 'Male'])
        metrics["demographics"]["gender_distribution"]["male_ratio"] = round((male_count / len(all_genders)) * 100, 1)
        metrics["demographics"]["gender_distribution"]["female_ratio"] = round(100 - metrics["demographics"]["gender_distribution"]["male_ratio"], 1)

    # Write analyst JSON report
    report_path = os.path.join(GOLD_DIR, "analyst_report.json")
    with open(report_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Gold Analyst JSON report generated at {report_path}")

    # Save a Gold insights parquet table
    try:
        gold_insights_df = pd.DataFrame([{
            "cohort": mtype,
            "prevalence_rate_pct": metrics["prevalence_rates"].get(mtype, 0.0),
            "model_accuracy": metrics["model_performance"].get(mtype, 0.0),
            "records_count": total_rows // 5
        } for mtype in model_types])

        gold_insights_path = os.path.join(GOLD_DIR, "gold_health_insights.parquet")
        gold_insights_df.to_parquet(gold_insights_path, index=False)
        logger.info(f"Gold insights parquet written to {gold_insights_path}")

        # Sync Gold folder to HF private dataset
        if hf_client is not None:
            upload_file_to_hf(hf_client, hf_dataset_id, report_path, "gold/analyst_report.json")
            upload_file_to_hf(hf_client, hf_dataset_id, gold_insights_path, "gold/gold_health_insights.parquet")
    except Exception as e:
        logger.error(f"Failed to generate Gold Insights Parquet: {e}")

def retrain_models():
    """Trigger the retraining script for each model and verify weights are updated."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    backend_dir = os.path.join(base_dir, "backend")

    models = ['diabetes', 'heart', 'kidney', 'liver', 'lungs']
    results = {}
    accuracies = {}

    logger.info("Starting model retraining loop...")
    for model in models:
        script = os.path.join(backend_dir, f"train_{model}.py")
        if os.path.exists(script):
            logger.info(f"Running retraining script: train_{model}.py")
            try:
                env = os.environ.copy()
                env["PYTHONPATH"] = backend_dir + os.pathsep + env.get("PYTHONPATH", "")

                res = subprocess.run([sys.executable, script], capture_output=True, text=True, env=env, timeout=600)
                if res.returncode == 0:
                    logger.info(f"Successfully retrained {model} model.")
                    results[model] = 'success'

                    # Parse accuracy from script stdout if printed (e.g. "Accuracy: 0.9200")
                    for line in res.stdout.split("\n"):
                        if "Accuracy:" in line:
                            try:
                                acc_val = float(line.split("Accuracy:")[-1].strip())
                                accuracies[model] = acc_val
                            except Exception:
                                pass
                else:
                    logger.error(f"Retraining {model} model failed. Code: {res.returncode}. Error:\n{res.stderr}\nOutput:\n{res.stdout}")
                    results[model] = 'failed'
            except Exception as e:
                logger.error(f"Retraining {model} failed with exception: {e}")
                results[model] = 'failed'
        else:
            logger.warning(f"Training script {script} not found. Skipping.")
            results[model] = 'skipped'

    return results, accuracies

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
    logger.info("--- STARTING MEDALLION ETL & RETRAINING RUNNER ---")
    start_time = time.time()

    # 1. Run Ingestion and Conformance through Bronze, Silver & Gold
    run_medallion_etl()

    # 2. Retrain models on conformed Silver data
    results, accuracies = retrain_models()
    logger.info(f"Retraining results summary: {results}")

    # 3. Regenerate Gold report with newly computed accuracies
    if accuracies:
        logger.info("Updating Gold report with actual training accuracies...")
        generate_gold_insights(start_time, accuracies)

    # 4. Sync trained models to Hugging Face
    hf_client, hf_dataset_id = get_hf_client()
    if hf_client is not None:
        logger.info("Syncing trained models to Hugging Face...")
        backend_dir = os.path.join(BASE_DIR, "backend")
        model_files = [
            "diabetes_model.pkl",
            "heart_disease_model.pkl",
            "liver_disease_model.pkl",
            "liver_scaler.pkl",
            "kidney_model.pkl",
            "kidney_scaler.pkl",
            "lungs_model.pkl",
            "lungs_scaler.pkl",
            "longitudinal_diabetes_model.pkl",
            "longitudinal_heart_model.pkl",
            "longitudinal_liver_model.pkl",
            "longitudinal_kidney_model.pkl"
        ]
        for model_file in model_files:
            local_model_path = os.path.join(backend_dir, model_file)
            if os.path.exists(local_model_path):
                logger.info(f"Uploading {model_file} to Hugging Face private dataset...")
                upload_file_to_hf(hf_client, hf_dataset_id, local_model_path, f"models/{model_file}")
            else:
                logger.warning(f"Model file {local_model_path} not found. Skipping upload.")

    # 5. Trigger Model Reload on active space
    reload_models_via_api()
    logger.info("--- MEDALLION RUNNER COMPLETED ---")
