import os
import sys
import json
import shutil
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("KaggleTrigger")

def setup_kaggle_credentials():
    """Read Kaggle credentials from environment or .env and write to ~/.kaggle/kaggle.json"""
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    
    # Try reading from .env if not in environment
    if not username or not key:
        dot_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        if os.path.exists(dot_env_path):
            with open(dot_env_path, "r") as f:
                for line in f:
                    if "=" in line:
                        parts = line.strip().split("=", 1)
                        if parts[0] == "KAGGLE_USERNAME":
                            username = parts[1].strip('"').strip("'")
                        elif parts[0] == "KAGGLE_KEY":
                            key = parts[1].strip('"').strip("'")
                            
    if not username or not key:
        raise RuntimeError("Kaggle credentials not found. Please set KAGGLE_USERNAME and KAGGLE_KEY in your environment or .env file.")
        
    # Write to standard Kaggle config directory
    home_dir = os.path.expanduser("~")
    kaggle_config_dir = os.path.join(home_dir, ".kaggle")
    os.makedirs(kaggle_config_dir, exist_ok=True)
    
    kaggle_json_path = os.path.join(kaggle_config_dir, "kaggle.json")
    with open(kaggle_json_path, "w") as f:
        json.dump({"username": username, "key": key}, f)
        
    # Ensure correct permissions (especially on Unix/Linux)
    try:
        os.chmod(kaggle_json_path, 0o600)
    except Exception:
        pass
        
    logger.info("Successfully configured Kaggle API credentials.")
    return username

def build_kaggle_kernel(username):
    """Create a folder with the notebook and metadata file for the Kaggle API."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    build_dir = os.path.join(base_dir, "kaggle_build")
    os.makedirs(build_dir, exist_ok=True)
    
    # 1. Create the Jupyter Notebook content
    notebook_content = {
      "cells": [
        {
          "cell_type": "markdown",
          "metadata": {},
          "source": [
            "# 🏥 AI Healthcare System - Weekly PySpark ETL & ML Retraining\n",
            "This notebook runs the ETL and model training in the cloud using Kaggle's free resources."
          ]
        },
        {
          "cell_type": "code",
          "execution_count": None,
          "metadata": {},
          "outputs": [],
          "source": [
            "# Clone the repository and install packages\n",
            "!git clone https://github.com/pavanbadempet/AI-Healthcare-System.git\n",
            "%cd AI-Healthcare-System\n",
            "!pip install pyspark delta-spark xgboost scikit-learn pandas sqlalchemy psycopg2-binary requests"
          ]
        },
        {
          "cell_type": "code",
          "execution_count": None,
          "metadata": {},
          "outputs": [],
          "source": [
            "import os\n",
            "# Run the Spark ETL script (database and HF reload credentials)\n",
            "os.environ[\"DATABASE_URL\"] = \"your_database_url_here\"\n",
            "os.environ[\"BACKEND_URL\"] = \"https://pavanbadempet-ai-healthcare-system.hf.space\"\n",
            "os.environ[\"ADMIN_JWT_TOKEN\"] = \"your_admin_jwt_token_here\"\n",
            "\n",
            "!python scripts/runners/run_spark_etl.py"
          ]
        }
      ],
      "metadata": {
        "kernelspec": {
          "display_name": "Python 3",
          "language": "python",
          "name": "python3"
        }
      },
      "nbformat": 4,
      "nbformat_minor": 0
    }
    
    notebook_path = os.path.join(build_dir, "healthcare_retrain_notebook.ipynb")
    with open(notebook_path, "w") as f:
        json.dump(notebook_content, f, indent=2)
        
    # 2. Create the Kaggle metadata configuration
    metadata = {
      "id": f"{username}/healthcare-retrain-pipeline",
      "title": "Healthcare Retrain Pipeline",
      "code_file": "healthcare_retrain_notebook.ipynb",
      "language": "python",
      "kernel_type": "notebook",
      "is_private": "true",
      "enable_gpu": "false",
      "enable_tpu": "false",
      "enable_internet": "true",
      "dataset_sources": [],
      "kernel_sources": [],
      "competition_sources": []
    }
    
    metadata_path = os.path.join(build_dir, "kernel-metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Built Kaggle kernel files in {build_dir}")
    return build_dir

def push_to_kaggle(build_dir, username):
    """Execute kaggle CLI or python API to push and run the kernel in the cloud."""
    # Install the official kaggle pip package if not present
    try:
        import kaggle
    except ImportError:
        logger.info("Installing official 'kaggle' API python package...")
        subprocess.run([sys.executable, "-m", "pip", "install", "kaggle"], check=True)
        
    # Trigger kernel push
    logger.info("Pushing and launching the kernel on Kaggle's cloud servers...")
    try:
        res = subprocess.run(
            ["kaggle", "kernels", "push", "-p", build_dir],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Kaggle push successful: {res.stdout.strip()}")
        logger.info(f"Your kernel is running in the cloud at: https://www.kaggle.com/{username}/healthcare-retrain-pipeline")
    except Exception as e:
        logger.error(f"Failed to push kernel to Kaggle: {e}")
        # Clean up config files
        raise

if __name__ == "__main__":
    logger.info("--- Programmatic Kaggle Cloud Retrain Trigger ---")
    try:
        username = setup_kaggle_credentials()
        build_dir = build_kaggle_kernel(username)
        push_to_kaggle(build_dir, username)
        
        # Clean up local temporary build directory
        shutil.rmtree(build_dir)
        logger.info("Cleaned up local build directory.")
        logger.info("--- Launch Sequence Finished ---")
    except Exception as e:
        logger.error(f"Error: {e}")
