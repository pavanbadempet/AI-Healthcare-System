import os
import requests
import logging

import sys
# Configure Logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ingestion.log')
    ]
)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# Dataset URLs (Real World Large Datasets)
DATASETS = {
    # 1. Diabetes (CDC BRFSS 2015)
    "diabetes_large.csv": "https://raw.githubusercontent.com/Helmy2/Diabetes-Health-Indicators/main/diabetes_binary_health_indicators_BRFSS2015.csv",
    
    # 2. Heart Disease (CDC BRFSS 2015)
    "heart_large.csv": "https://raw.githubusercontent.com/alexteboul/Heart-Disease-Health-Indicators-Dataset/main/heart_disease_health_indicators_BRFSS2015.csv",
    
    # 3. Liver Disease (UCI ILPD)
    "liver_large.csv": "https://raw.githubusercontent.com/dasarpai/DAI-Datasets/main/Liver_Patient/Liver%20Patient%20Dataset%20(LPD)_train.csv",
    
    # 4. Kidney Disease (UCI Chronic Kidney Disease) - Verified URL
    "kidney.csv": "https://raw.githubusercontent.com/aiplanethub/Datasets/master/Chronic%20Kidney%20Disease%20(CKD)%20Dataset/ChronicKidneyDisease.csv",
    
    # 5. Respiratory/Lung Cancer (Rashida048/Yanne0800) - Verified URL
    "lungs.csv": "https://raw.githubusercontent.com/Yanne0800/Lung_Cancer_Prediction/main/survey_lung_cancer.csv"
}

def download_file(url, filename):
    filepath = os.path.join(RAW_DIR, filename)
    
    # Force overwrite if file is small (likely synthetic) or doesn't exist.
    # We want to replace the synthetic 1KB files with real ones.
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        if size < 5000: # If smaller than 5KB, it's synthetic/broken. Redownload.
            logger.info(f"Replacing small/synthetic file: {filename} ({size} bytes)")
            os.remove(filepath)
        else:
            logger.info(f"File already exists and looks valid: {filename} (Size: {size})")
            return filepath
    
    logger.info(f"Downloading {filename} from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"✔ Successfully downloaded {filename}")
        return filepath
    except Exception as e:
        logger.error(f"❌ Failed to download {filename}: {e}")
        return None

if __name__ == "__main__":
    logger.info("--- Starting Large Dataset Ingestion (Real Sources) ---")
    for name, url in DATASETS.items():
        download_file(url, name)
    logger.info("--- Ingestion Complete ---")
