"""
Model Monitor — Prediction Drift & Performance Tracker
======================================================
Calculates statistical drift (PSI, KS Test, Chi-Squared) and tracks model accuracy
degradation using sliding windows over prediction history.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PredictionRecord:
    model_name: str
    features: Dict[str, Any]
    prediction: Any
    confidence: float
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())

class ModelMonitor:
    """Thread-safe singleton for model performance and data drift monitoring."""
    _instance: Optional[ModelMonitor] = None
    _lock = threading.Lock()

    def __new__(cls) -> ModelMonitor:
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._init_monitor()
                cls._instance = inst
            return cls._instance

    def _init_monitor(self) -> None:
        self._lock = threading.Lock()
        self._history: Dict[str, List[PredictionRecord]] = {}
        self._max_window_size = 10000

    def record_prediction(self, model_name: str, features: Dict[str, Any], prediction: Any, confidence: float) -> None:
        """Saves a prediction trace to the monitoring buffer."""
        with self._lock:
            if model_name not in self._history:
                self._history[model_name] = []

            self._history[model_name].append(
                PredictionRecord(
                    model_name=model_name,
                    features=features,
                    prediction=prediction,
                    confidence=confidence
                )
            )

            # Evict oldest if exceeding size
            if len(self._history[model_name]) > self._max_window_size:
                self._history[model_name].pop(0)

    def calculate_psi(self, model_name: str, reference_features: List[float], current_features: List[float], num_buckets: int = 10) -> float:
        """Calculates Population Stability Index (PSI) between reference and current feature distributions."""
        ref_arr = np.array(reference_features)
        curr_arr = np.array(current_features)

        if ref_arr.size == 0 or curr_arr.size == 0:
            return 0.0

        percentiles = np.linspace(0, 100, num_buckets + 1)
        buckets = np.percentile(ref_arr, percentiles)
        buckets[0] = -np.inf
        buckets[-1] = np.inf

        ref_counts, _ = np.histogram(ref_arr, bins=buckets)
        curr_counts, _ = np.histogram(curr_arr, bins=buckets)

        ref_pcts = ref_counts / len(ref_arr)
        curr_pcts = curr_counts / len(curr_arr)

        # Handle zero counts using minor smoothing to avoid division by zero / log(0)
        ref_pcts = np.where(ref_pcts == 0, 0.0001, ref_pcts)
        curr_pcts = np.where(curr_pcts == 0, 0.0001, curr_pcts)

        psi = np.sum((curr_pcts - ref_pcts) * np.log(curr_pcts / ref_pcts))
        return float(psi)

    def calculate_feature_drift(self, model_name: str, feature_name: str, reference_data: List[Any]) -> Dict[str, Any]:
        """Performs Kolmogorov-Smirnov (KS) test for numerical or Chi-Squared for categorical features."""
        with self._lock:
            history = self._history.get(model_name, [])
            current_data = [h.features.get(feature_name) for h in history if feature_name in h.features]

        if not current_data or not reference_data:
            return {"drift_detected": False, "p_value": 1.0, "test_name": "unknown"}

        try:
            from scipy import stats

            # Check if feature is numerical
            is_numeric = all(isinstance(x, (int, float, np.number)) and not isinstance(x, bool) for x in current_data)

            if is_numeric:
                ks_stat, p_value = stats.ks_2samp(reference_data, current_data)
                # p_value < 0.05 indicates the distributions differ (drift)
                return {
                    "drift_detected": p_value < 0.05,
                    "p_value": float(p_value),
                    "statistic": float(ks_stat),
                    "test_name": "Kolmogorov-Smirnov"
                }
            else:
                # Categorical -> Chi-Square
                ref_unique, ref_counts = np.unique(reference_data, return_counts=True)
                curr_unique, curr_counts = np.unique(current_data, return_counts=True)

                # Align categories
                all_cats = list(set(ref_unique).union(set(curr_unique)))
                ref_dist = {cat: 0 for cat in all_cats}
                curr_dist = {cat: 0 for cat in all_cats}

                for cat, count in zip(ref_unique, ref_counts):
                    ref_dist[cat] = count
                for cat, count in zip(curr_unique, curr_counts):
                    curr_dist[cat] = count

                ref_freq = [ref_dist[cat] for cat in all_cats]
                curr_freq = [curr_dist[cat] for cat in all_cats]

                # Normalize frequencies to probabilities, then scale current frequencies to match total reference samples
                total_ref = sum(ref_freq)
                total_curr = sum(curr_freq)

                if total_ref == 0 or total_curr == 0:
                    return {"drift_detected": False, "p_value": 1.0, "test_name": "Chi-Square"}

                expected = np.array(ref_freq) / total_ref * total_curr
                observed = np.array(curr_freq)

                # Avoid zero expectations
                expected = np.where(expected == 0, 0.0001, expected)
                chi_stat, p_value = stats.chisquare(observed, f_exp=expected)

                return {
                    "drift_detected": p_value < 0.05,
                    "p_value": float(p_value),
                    "statistic": float(chi_stat),
                    "test_name": "Chi-Square"
                }
        except ImportError:
            logger.warning("scipy not installed. Skipping statistical drift tests.")
            return {"drift_detected": False, "p_value": 1.0, "test_name": "Fallback (no scipy)"}
        except Exception as e:
            logger.error("Drift calculation failed: %s", e)
            return {"drift_detected": False, "p_value": 1.0, "test_name": "Error"}

    def get_drift_report(self, model_name: str, reference_datasets: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Generates statistical drift summaries across all features of a model."""
        report = {}
        for feature_name, ref_data in reference_datasets.items():
            report[feature_name] = self.calculate_feature_drift(model_name, feature_name, ref_data)
        return report

    def check_accuracy_degradation(self, model_name: str, actuals: List[Tuple[Any, Any]], window_size: int = 1000) -> float:
        """Calculates model accuracy over the last N actual outcomes."""
        if not actuals:
            return 1.0

        recent = actuals[-window_size:]
        correct = sum(1 for pred, actual in recent if str(pred).lower() == str(actual).lower())
        return correct / len(recent)

    def get_alert_status(self, model_name: str, current_psi: float, current_accuracy: float, baseline_accuracy: float) -> str:
        """Calculates warning thresholds: PSI > 0.25 is critical, accuracy drop > 5% is warning."""
        if current_psi > 0.25 or (baseline_accuracy - current_accuracy) > 0.10:
            return "CRITICAL"
        elif current_psi > 0.10 or (baseline_accuracy - current_accuracy) > 0.05:
            return "WARNING"
        return "OK"

# Global instance
model_monitor = ModelMonitor()
