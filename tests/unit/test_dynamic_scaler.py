"""
Unit tests for Dynamic Clinical Feature Scaler.
"""

import numpy as np

from backend.dynamic_scaler import DynamicClinicalScaler, scale_features_dynamically


def test_dynamic_clinical_scaler_zscore():
    X = np.array([[10, 100], [20, 200], [30, 300]], dtype=float)
    scaler = DynamicClinicalScaler()
    scaled = scaler.fit(X).transform_zscore(X)
    assert scaled.shape == (3, 2)
    assert np.allclose(np.mean(scaled, axis=0), [0.0, 0.0])


def test_scale_features_dynamically():
    bounds = {0: (0.0, 100.0), 1: (50.0, 250.0)}
    raw = [50.0, 150.0]
    scaled = scale_features_dynamically(raw, bounds)
    assert scaled[0] == 0.5
    assert scaled[1] == 0.5
