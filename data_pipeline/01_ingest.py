import pandas as pd
import os
import sys

def ingest_data(input_path, output_path):
    print(f"Reading data from {input_path}...")
    
    try:
        # Read CSV
        df = pd.read_csv(input_path)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print("Data Schema:")
    print(df.info())

    # Basic Cleaning: Drop rows with all nulls
    initial_rows = len(df)
    df_clean = df.dropna(how="all")
    print(f"Dropped {initial_rows - len(df_clean)} empty rows.")

    # Ensure numerical columns are cast correctly
    # ( Pandas infers types automatically, but good to be explicit for 'ETL' )
    cols_to_cast = ["age", "bmi", "HbA1c_level", "blood_glucose_level"]
    for c in cols_to_cast:
        if c in df_clean.columns:
            df_clean[c] = pd.to_numeric(df_clean[c], errors='coerce')

    print(f"Saving processed data to {output_path}...")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save as Parquet (Requires pyarrow or fastparquet, usually installed with pandas in modern envs)
    # If parquet fails, we can fall back or user needs `pip install pyarrow`
    try:
        df_clean.to_parquet(output_path, index=False)
        print("Ingestion Complete.")
    except ImportError:
        print("Error: Pyarrow not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyarrow"])
        df_clean.to_parquet(output_path, index=False)
        print("Ingestion Complete (after installing pyarrow).")

if __name__ == "__main__":
    input_file = "data/raw/test_data.csv"
    output_path = "data/processed/test_data.parquet"
    
    if not os.path.exists(input_file):
        print(f"Please create '{input_file}' to test.")
    else:
        ingest_data(input_file, output_path)
