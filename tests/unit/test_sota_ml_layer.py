"""
Unit tests for SOTA Accelerated ML Engine (backend/sota_ml_layer.py).
"""

from backend.sota_ml_layer import SOTAMLLayerEngine


def test_ml_inference_calibration_and_drift_detection():
    engine = SOTAMLLayerEngine()

    normal_features = {"age": 45.0, "heart_rate": 75.0, "systolic_bp": 120.0}
    output = engine.predict_readmission_risk(normal_features)

    assert output.model_version == "v2.4.0-onnx-quantized"
    assert 0.0 <= output.calibrated_probability <= 1.0
    assert not output.is_drift_detected
    assert "heart_rate" in output.feature_attributions

    # Test drift detection with abnormal feature spike
    drifted_features = {"age": 45.0, "heart_rate": 160.0, "systolic_bp": 210.0}
    output_drifted = engine.predict_readmission_risk(drifted_features)

    assert output_drifted.is_drift_detected
    assert output_drifted.prediction_class == 1
