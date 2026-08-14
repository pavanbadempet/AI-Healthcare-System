"""
Test Suite for Real Clinical Dataset Loader & Standardized Cohort Generator:
- CDC BRFSS Diabetes & Heart Disease Data Loading
- Indian Liver Patient Dataset Loading
- Unified Multi-Condition Clinical Cohort Generation (Epidemiological Co-variance)
"""

import pytest
from backend.data_platform.real_dataset_loader import real_dataset_loader, RealClinicalDatasetLoader


def test_cdc_diabetes_dataset_loading():
    """Verifies that the CDC BRFSS Diabetes dataset is loaded from processed parquets."""
    df = real_dataset_loader.load_cdc_diabetes_cohort(limit=100)
    assert len(df) == 100
    assert "BMI" in df.columns
    assert "HighBP" in df.columns
    assert "diabetes" in df.columns


def test_cdc_heart_dataset_loading():
    """Verifies that the CDC BRFSS Heart Disease dataset is loaded."""
    df = real_dataset_loader.load_cdc_heart_cohort(limit=100)
    assert len(df) == 100
    assert "target" in df.columns or "high_bp" in df.columns or "HeartDiseaseorAttack" in df.columns



def test_liver_dataset_loading():
    """Verifies that the Liver disease dataset is loaded."""
    df = real_dataset_loader.load_liver_cohort(limit=100)
    assert len(df) == 100
    assert "Age" in df.columns or "age" in df.columns or len(df.columns) >= 5


def test_unified_clinical_cohort_generation():
    """Verifies unified patient cohort with true physiological measurements & conditions."""
    cohort = real_dataset_loader.load_unified_clinical_cohort(sample_size=200)
    assert len(cohort) == 200

    sample = cohort[0]
    assert "patient_id" in sample
    assert "systolic_bp" in sample
    assert "fasting_glucose" in sample
    assert "hba1c" in sample
    assert "conditions" in sample
    assert "medications" in sample
    assert len(sample["conditions"]) >= 1
