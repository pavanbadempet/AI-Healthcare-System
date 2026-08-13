"""
Comprehensive Test Suite for PySpark ML & Distributed Data Engineering Platform:
- PySpark ML Pipeline Construction (VectorAssembler, StandardScaler, RandomForest)
- Distributed Evaluation Metrics (ROC-AUC, PR-AUC, Accuracy, F1-Score)
- Vectorized Batch Inference & Risk Scoring
- SparkConnect Session & Zero-Config Sandbox Validation
"""

import pytest
from backend.ml.pyspark_ml_pipeline import pyspark_ml_engine, PySparkPipelineConfig, PySparkClinicalMLEngine
from backend.spark_engine import spark4_variant_handler, SparkConnectManager


def test_pyspark_ml_pipeline_config():
    """Verifies that PySpark pipeline configuration initializes standard clinical features."""
    config = PySparkPipelineConfig(num_trees=50, max_depth=6)
    assert len(config.feature_columns) == 8
    assert "fasting_glucose" in config.feature_columns
    assert "hba1c" in config.feature_columns
    assert config.num_trees == 50


def test_pyspark_ml_train_and_evaluate():
    """Verifies that PySpark ML engine computes valid classification metrics."""
    result = pyspark_ml_engine.train_and_evaluate()
    assert result["status"] == "TRAINING_COMPLETE"
    assert "metrics" in result
    
    metrics = result["metrics"]
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert 0.0 <= metrics["pr_auc"] <= 1.0
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["f1_score"] <= 1.0
    assert metrics["roc_auc"] >= 0.85


def test_pyspark_ml_batch_prediction():
    """Verifies distributed risk scoring across patient batch records."""
    batch = [
        {"patient_id": "P-101", "age": 65, "fasting_glucose": 175, "systolic_bp": 150, "hba1c": 8.5, "bmi": 32},
        {"patient_id": "P-102", "age": 30, "fasting_glucose": 88, "systolic_bp": 115, "hba1c": 5.2, "bmi": 22}
    ]

    scored = pyspark_ml_engine.predict_batch_records(batch)
    assert len(scored) == 2
    
    # High risk patient P-101
    p1 = scored[0]
    assert p1["pyspark_predicted_label"] == 1
    assert p1["pyspark_risk_probability"] > 0.60
    assert p1["risk_tier"] == "HIGH RISK"

    # Low risk patient P-102
    p2 = scored[1]
    assert p2["pyspark_predicted_label"] == 0
    assert p2["pyspark_risk_probability"] < 0.35
    assert p2["risk_tier"] == "LOW RISK"


def test_spark_variant_json_shredding():
    """Verifies that Spark 4.0 Variant JSON handler shreds semi-structured FHIR blobs."""
    fhir_blob = {
        "resourceType": "Observation",
        "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}]},
        "valueQuantity": {"value": 78, "unit": "beats/minute"}
    }

    shredded = spark4_variant_handler.shred_variant_json(fhir_blob, target_paths=["resourceType", "valueQuantity.value"])
    assert shredded["resourceType"] == "Observation"
    assert shredded["valueQuantity.value"] == 78
