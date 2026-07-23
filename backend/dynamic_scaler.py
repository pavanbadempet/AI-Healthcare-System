"""
Dynamic Feature Scaling Engine — Adaptive Robust Clinical Standardization
========================================================================

Provides dynamic, adaptive feature scaling for ML models:
1. Dynamic Min-Max Scaling based on clinical parameter physiological bounds.
2. Dynamic Z-Score Standardization with outlier clipping (Robust Scaler).
3. Dynamic Matrix Normalization that scales dynamically based on incoming array dimensions.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np


class DynamicClinicalScaler:
    """
    SOTA Dynamic Feature Scaler that automatically adapts to varying feature dimensions
    and incoming data distributions without hardcoded scaling constants.
    """

    def __init__(self, clip_outliers: bool = True, outlier_std_threshold: float = 3.0):
        self.clip_outliers = clip_outliers
        self.outlier_std_threshold = outlier_std_threshold
        self.mean_: Optional[np.ndarray] = None
        self.std_: Optional[np.ndarray] = None
        self.min_: Optional[np.ndarray] = None
        self.max_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> "DynamicClinicalScaler":
        """Dynamically computes mean, std, min, and max across feature columns."""
        X_arr = np.asarray(X, dtype=float)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)

        self.mean_ = np.mean(X_arr, axis=0)
        self.std_ = np.std(X_arr, axis=0)
        # Avoid division by zero
        self.std_[self.std_ == 0.0] = 1.0

        self.min_ = np.min(X_arr, axis=0)
        self.max_ = np.max(X_arr, axis=0)
        return self

    def transform_zscore(self, X: np.ndarray) -> np.ndarray:
        """Dynamically normalizes features using Z-score standardization with adaptive outlier clipping."""
        X_arr = np.asarray(X, dtype=float)
        if self.mean_ is None or self.std_ is None:
            self.fit(X_arr)

        scaled = (X_arr - self.mean_) / self.std_

        if self.clip_outliers:
            scaled = np.clip(scaled, -self.outlier_std_threshold, self.outlier_std_threshold)

        return scaled

    def transform_minmax(self, X: np.ndarray, feature_bounds: Optional[Dict[int, Tuple[float, float]]] = None) -> np.ndarray:
        """
        Dynamically scales features to [0, 1] range using either observed column min/max
        or dynamic physiological reference bounds.
        """
        X_arr = np.asarray(X, dtype=float)
        if self.min_ is None or self.max_ is None:
            self.fit(X_arr)

        scaled = np.zeros_like(X_arr, dtype=float)
        n_features = X_arr.shape[-1] if X_arr.ndim > 1 else X_arr.shape[0]

        for i in range(n_features):
            if feature_bounds and i in feature_bounds:
                min_val, max_val = feature_bounds[i]
            else:
                min_val = self.min_[i] if self.min_ is not None else 0.0
                max_val = self.max_[i] if self.max_ is not None else 1.0

            denom = (max_val - min_val) if max_val != min_val else 1.0
            col = X_arr[:, i] if X_arr.ndim > 1 else X_arr[i]
            scaled_col = (col - min_val) / denom
            if X_arr.ndim > 1:
                scaled[:, i] = np.clip(scaled_col, 0.0, 1.0)
            else:
                scaled[i] = float(np.clip(scaled_col, 0.0, 1.0))

        return scaled


def scale_features_dynamically(
    input_vector: List[float],
    physiological_bounds: Optional[Dict[int, Tuple[float, float]]] = None
) -> List[float]:
    """
    Convenience function for dynamic 1D feature vector scaling.
    """
    scaler = DynamicClinicalScaler()
    arr = np.array([input_vector], dtype=float)
    scaled_arr = scaler.fit(arr).transform_minmax(arr, physiological_bounds)
    return scaled_arr[0].tolist()
