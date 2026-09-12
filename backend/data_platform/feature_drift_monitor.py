"""
Point-in-Time Feature Store Registry & Automated Drift Monitoring Engine.

Tracks feature distribution shifts over time using:
1. Population Stability Index (PSI) across quantile buckets:
   PSI = sum((P_b - Q_b) * ln(P_b / Q_b))
2. Wasserstein-1 Metric (Earth Mover's Distance).
3. Two-sample Kolmogorov-Smirnov (KS) goodness-of-fit test.
4. Automated alert triage (Normal, Moderate Drift, Critical Drift Requiring Model Retraining).
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy.stats import ks_2samp, wasserstein_distance

logger = logging.getLogger("backend.data_platform.drift")


@dataclass
class ClinicalFeatureDefinition:
    feature_name: str
    entity_type: str  # "PATIENT", "VISIT", "DEVICE"
    data_type: str  # "FLOAT", "INTEGER", "CATEGORICAL"
    description: str
    unit: str
    ttl_hours: int
    baseline_distribution: List[float]


@dataclass
class DriftAuditReport:
    feature_name: str
    sample_size_baseline: int
    sample_size_current: int
    psi_score: float
    wasserstein_distance_score: float
    ks_statistic: float
    ks_p_value: float
    drift_status: str  # "NORMAL", "MODERATE_SHIFT", "CRITICAL_DRIFT_ALERT"
    requires_retraining: bool
    recommended_action: str
    bucket_distributions: List[Dict[str, Any]]


class FeatureDriftMonitor:
    """
    Feature Store Governance and Real-Time Distribution Drift Monitor.
    """

    def __init__(self) -> None:
        self._rng = np.random.RandomState(42)
        self._registry: Dict[str, ClinicalFeatureDefinition] = self._initialize_feature_registry()

    def _initialize_feature_registry(self) -> Dict[str, ClinicalFeatureDefinition]:
        """
        Registers core clinical feature definitions with pre-calibrated baseline distributions.
        """
        registry = {}

        # 1. eGFR (Renal filtration rate)
        egfr_base = self._rng.normal(loc=72.0, scale=18.0, size=500).tolist()
        registry["egfr"] = ClinicalFeatureDefinition(
            feature_name="egfr",
            entity_type="PATIENT",
            data_type="FLOAT",
            description="Estimated Glomerular Filtration Rate via CKD-EPI equation",
            unit="mL/min/1.73m2",
            ttl_hours=720,  # 30 days
            baseline_distribution=egfr_base,
        )

        # 2. MAP (Mean Arterial Pressure in ICU)
        map_base = self._rng.normal(loc=78.0, scale=8.5, size=500).tolist()
        registry["map"] = ClinicalFeatureDefinition(
            feature_name="map",
            entity_type="PATIENT",
            data_type="FLOAT",
            description="Bedside continuous mean arterial blood pressure",
            unit="mmHg",
            ttl_hours=1,
            baseline_distribution=map_base,
        )

        # 3. Serum Lactate (Tissue hypoperfusion marker)
        lactate_base = self._rng.exponential(scale=1.4, size=500).tolist()
        registry["lactate"] = ClinicalFeatureDefinition(
            feature_name="lactate",
            entity_type="PATIENT",
            data_type="FLOAT",
            description="Arterial/Venous serum lactate concentration",
            unit="mmol/L",
            ttl_hours=4,
            baseline_distribution=lactate_base,
        )

        return registry

    def compute_psi(
        self,
        baseline: np.ndarray,
        current: np.ndarray,
        num_buckets: int = 10,
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Calculates Population Stability Index (PSI) using quantile binning:
        PSI = sum((Actual_pct - Expected_pct) * ln(Actual_pct / Expected_pct))
        """
        # Determine quantile boundaries from baseline
        quantiles = np.linspace(0.0, 100.0, num_buckets + 1)
        bins = np.percentile(baseline, quantiles)
        # Ensure strictly increasing bins
        bins[0] = -np.inf
        bins[-1] = np.inf
        for i in range(1, len(bins) - 1):
            if bins[i] <= bins[i - 1]:
                bins[i] = bins[i - 1] + 1e-5

        # Compute empirical counts
        base_counts, _ = np.histogram(baseline, bins=bins)
        curr_counts, _ = np.histogram(current, bins=bins)

        base_pcts = base_counts / len(baseline)
        curr_pcts = curr_counts / len(current)

        # Add tiny epsilon to avoid division by zero
        eps = 1e-4
        base_pcts = np.clip(base_pcts, eps, None)
        curr_pcts = np.clip(curr_pcts, eps, None)
        # Re-normalize
        base_pcts /= np.sum(base_pcts)
        curr_pcts /= np.sum(curr_pcts)

        # Calculate PSI
        psi_contributions = (curr_pcts - base_pcts) * np.log(curr_pcts / base_pcts)
        total_psi = float(np.sum(psi_contributions))

        bucket_info = []
        for b in range(num_buckets):
            bucket_info.append({
                "bucket_index": b,
                "expected_percentage": round(float(base_pcts[b]) * 100.0, 2),
                "actual_percentage": round(float(curr_pcts[b]) * 100.0, 2),
                "psi_contribution": round(float(psi_contributions[b]), 5),
            })

        return total_psi, bucket_info

    def audit_feature_drift(
        self,
        feature_name: str,
        current_samples: List[float],
    ) -> DriftAuditReport:
        """
        Runs comprehensive drift analysis comparing current telemetry against baseline.
        """
        feat_key = feature_name.lower().strip()
        defn = self._registry.get(feat_key)
        if not defn:
            raise ValueError(f"Feature '{feature_name}' is not registered in the feature store.")

        base_arr = np.array(defn.baseline_distribution, dtype=float)
        curr_arr = np.array(current_samples, dtype=float)

        if len(curr_arr) < 5:
            raise ValueError("At least 5 current observation samples are required for drift testing.")

        # 1. Population Stability Index (PSI)
        psi_score, bucket_info = self.compute_psi(base_arr, curr_arr, num_buckets=10)

        # 2. Wasserstein Distance
        w_dist = float(wasserstein_distance(base_arr, curr_arr))

        # 3. Kolmogorov-Smirnov Test
        ks_res = ks_2samp(base_arr, curr_arr)
        ks_stat = float(ks_res.statistic)
        ks_pval = float(ks_res.pvalue)

        # 4. Status Triage
        if psi_score < 0.10:
            status = "NORMAL"
            retrain = False
            action = "Distribution stable. No intervention required."
        elif psi_score < 0.25:
            status = "MODERATE_SHIFT"
            retrain = False
            action = "Moderate covariate shift observed. Increase monitoring frequency."
        else:
            status = "CRITICAL_DRIFT_ALERT"
            retrain = True
            action = "Substantial covariate drift detected (PSI >= 0.25). Trigger clinical model retraining pipeline."

        return DriftAuditReport(
            feature_name=feature_name,
            sample_size_baseline=len(base_arr),
            sample_size_current=len(curr_arr),
            psi_score=round(psi_score, 4),
            wasserstein_distance_score=round(w_dist, 4),
            ks_statistic=round(ks_stat, 4),
            ks_p_value=round(ks_pval, 4),
            drift_status=status,
            requires_retraining=retrain,
            recommended_action=action,
            bucket_distributions=bucket_info,
        )


feature_drift_monitor = FeatureDriftMonitor()
