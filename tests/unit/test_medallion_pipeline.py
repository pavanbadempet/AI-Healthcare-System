import os
import polars as pl
from scripts.run_medallion_pipeline import run_medallion_pipeline, LAKEHOUSE_ROOT

def test_medallion_pipeline_execution():
    """Verify that the medallion lakehouse pipeline runs successfully and writes tables to disk"""
    # Run the pipeline
    run_medallion_pipeline()
    
    # Assert directories exist
    assert os.path.exists(LAKEHOUSE_ROOT)
    assert os.path.exists(os.path.join(LAKEHOUSE_ROOT, "bronze", "patients"))
    assert os.path.exists(os.path.join(LAKEHOUSE_ROOT, "silver", "patients"))
    assert os.path.exists(os.path.join(LAKEHOUSE_ROOT, "gold", "patient_summary"))
    
    # Verify silver deduplicated count is 3
    df_silver = pl.read_delta(os.path.join(LAKEHOUSE_ROOT, "silver", "patients"))
    assert len(df_silver) == 3
    
    # Verify gold demographics summary aggregates by gender
    df_gold = pl.read_delta(os.path.join(LAKEHOUSE_ROOT, "gold", "patient_summary"))
    assert len(df_gold) > 0
    assert "gender" in df_gold.columns
