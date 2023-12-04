import pandas as pd
import numpy as np
import os
import sys
# Configure Logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('processing.log')
    ]
)
logger = logging.getLogger(__name__)
    
    if not os.path.exists(input_path):
        logger.warning(f"Input file not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    
    # Rename target to generic 'target'
    df.rename(columns={'Diabetes_binary': 'diabetes'}, inplace=True)
    
    # Save as Parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"✔ Saved {output_path} with shape {df.shape}")

def process_heart_cdc():
    logger.info("Processing Heart Dataset (CDC BRFSS 2015)...")
    # We use the SAME source file as Diabetes, but different target
    input_path = os.path.join(RAW_DIR, "diabetes_large.csv") 
    output_path = os.path.join(PROCESSED_DIR, "heart.parquet")
    
    if not os.path.exists(input_path):
        logger.warning(f"Input file not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    
    # Target: HeartDiseaseorAttack
    # Features: HighBP, HighChol, BMI, Smoker, Stroke, Diabetes_binary, PhysActivity, HvyAlcoholConsump, GenHlth, Sex, Age
    
    # Rename for consistency
    df.rename(columns={
        'HeartDiseaseorAttack': 'target',
        'Diabetes_binary': 'diabetes',
        'HighBP': 'high_bp',
        'HighChol': 'high_chol',
        'BMI': 'bmi',
        'Smoker': 'smoker',
        'Stroke': 'stroke',
        'PhysActivity': 'phys_activity',
        'HvyAlcoholConsump': 'hvy_alcohol',
        'GenHlth': 'gen_hlth',
        'Sex': 'sex',
        'Age': 'age'
    }, inplace=True)
    
    # Select only relevant columns to avoid noise
    keep_cols = ['target', 'high_bp', 'high_chol', 'bmi', 'smoker', 'stroke', 'diabetes', 'phys_activity', 'hvy_alcohol', 'gen_hlth', 'sex', 'age']
    df = df[keep_cols]
    
    # Save
    df.to_parquet(output_path, index=False)
    logger.info(f"✔ Saved {output_path} with shape {df.shape}")

def process_liver():
    logger.info("Processing Liver Dataset...")
    input_path = os.path.join(RAW_DIR, "liver_large.csv")
    output_path = os.path.join(PROCESSED_DIR, "liver.parquet")
    
    if not os.path.exists(input_path):
        logger.warning(f"Input file not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    
    # Clean Column Names
    df.columns = [c.strip().replace(' ', '_').lower() for c in df.columns]
    
    # Handle Target (Dataset specific mapping)
    if 'dataset' in df.columns:
        # 1 = Disease, 2 = No Disease (ILPD standard) -> Map to 1/0
        df['target'] = df['dataset'].map({1: 1, 2: 0})
        df.drop(columns=['dataset'], inplace=True)
    
    # Handle Categorical (Gender)
    if 'gender' in df.columns:
        df['gender'] = df['gender'].map({'Male': 1, 'Female': 0})
    
    # Fill Missing
    df.fillna(df.mean(), inplace=True)
    
    df.to_parquet(output_path, index=False)
    logger.info(f"✔ Saved {output_path} with shape {df.shape}")

def process_kidney():
    logger.info("Processing Kidney Dataset...")
    input_path = os.path.join(RAW_DIR, "kidney.csv")
    output_path = os.path.join(PROCESSED_DIR, "kidney.parquet")
    
    if not os.path.exists(input_path):
        logger.warning(f"Input file not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    
    # 1. Clean Column Names
    df.columns = [c.strip().replace(' ', '_').lower() for c in df.columns]
    
    # 2. Map Categoricals (CKD Dataset is very messy with tabs/nan)
    # Target: ckd/notckd
    df['classification'] = df['classification'].astype(str).str.strip()
    df['target'] = df['classification'].map({'ckd': 1, 'ckd\t': 1, 'notckd': 0})
    
    # Binary Features
    # rbc, pc -> normal/abnormal
    mapping_binary = {'normal': 0, 'abnormal': 1, 'present': 1, 'notpresent': 0}
    for col in ['rbc', 'pc', 'pcc', 'ba']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().map(mapping_binary)
            
    # Yes/No Features
    # htn, dm, cad, appet, pe, ane
    mapping_yesno = {'yes': 1, 'no': 0, '\tyes': 1, '\tno': 0, ' good': 0, 'poor': 1, 'good': 0}
    for col in ['htn', 'dm', 'cad', 'appet', 'pe', 'ane']:
         if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace(mapping_yesno)
            # Handle stubborn strings
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Numerical Cleaning (Remove \t, ?, etc)
    for col in df.columns:
        if df[col].dtype == 'object':
             # Try converting to numeric if it looks like one
             df[col] = pd.to_numeric(df[col].astype(str).str.replace('\t', ''), errors='ignore')

    # Drop ID
    df.drop(columns=['id'], inplace=True, errors='ignore')

    # Fill Missing (Critical for this small dataset ~400 rows)
    # Mode for categorical, Median for numerical
    for col in df.columns:
        if df[col].dtype == 'object' or len(df[col].unique()) < 10:
             df[col] = df[col].fillna(df[col].mode()[0])
        else:
             df[col] = df[col].fillna(df[col].median())
             
    # Ensure numeric types
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df.to_parquet(output_path, index=False)
    logger.info(f"✔ Saved {output_path} with shape {df.shape}")

def process_lungs():
    logger.info("Processing Lung Dataset...")
    input_path = os.path.join(RAW_DIR, "lungs.csv")
    output_path = os.path.join(PROCESSED_DIR, "lungs.parquet")
    
    if not os.path.exists(input_path):
        logger.warning(f"Input file not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    
    # Clean Columns
    df.columns = [c.strip().replace(' ', '_').upper() for c in df.columns]
    
    # Mappings
    # Dataset convention: 2=Yes, 1=No -> Convert to 1=Yes, 0=No
    # Gender: M/F
    
    if 'GENDER' in df.columns:
        df['GENDER'] = df['GENDER'].map({'M': 1, 'F': 0})
        
    for col in df.columns:
        if col not in ['AGE', 'GENDER']:
            # Map YES/NO strings if present
            if df[col].dtype == 'object':
                 df[col] = df[col].map({'YES': 1, 'NO': 0})
            else:
                 # Map 2->1, 1->0
                 df[col] = df[col].map({2: 1, 1: 0})
                 
    # Rename Target
    if 'LUNG_CANCER' in df.columns:
        df.rename(columns={'LUNG_CANCER': 'target'}, inplace=True)
        
    df.to_parquet(output_path, index=False)
    logger.info(f"✔ Saved {output_path} with shape {df.shape}")

if __name__ == "__main__":
    process_diabetes()
    process_heart_cdc()
    process_liver()
    process_kidney()
    process_lungs()
