"""
Feature Store Client — Feast Online & Offline Feature Retrieval
================================================================
Thread-safe singleton wrapper around Feast for serving real-time
features and creating training datasets.

Falls back silently when Feast is not configured or unavailable,
following the same graceful-degradation pattern used by
:pymod:`backend.cache_service`.

Usage::

    from backend.feature_store_client import feature_store_client

    features = feature_store_client.get_online_features(
        entity_ids=[{"patient_id": 42}],
        feature_refs=["patient_vitals:heart_rate", "patient_vitals:blood_pressure"],
    )
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

FEAST_REPO_PATH = os.environ.get("FEAST_REPO_PATH", None)


# ── Feature Group Definitions ────────────────────────────────────────


@dataclass(frozen=True)
class FeatureGroup:
    """Metadata describing a logical group of Feast features."""

    name: str
    entity: str
    features: List[str] = field(default_factory=list)
    description: str = ""


# Healthcare-domain feature groups
FEATURE_GROUPS: Dict[str, FeatureGroup] = {
    "patient_demographics": FeatureGroup(
        name="patient_demographics",
        entity="patient_id",
        features=[
            "patient_demographics:age",
            "patient_demographics:gender",
            "patient_demographics:bmi",
            "patient_demographics:smoking_status",
        ],
        description="Static demographic features for a patient.",
    ),
    "patient_vitals": FeatureGroup(
        name="patient_vitals",
        entity="patient_id",
        features=[
            "patient_vitals:heart_rate",
            "patient_vitals:blood_pressure_systolic",
            "patient_vitals:blood_pressure_diastolic",
            "patient_vitals:temperature",
            "patient_vitals:respiratory_rate",
            "patient_vitals:oxygen_saturation",
        ],
        description="Latest vital-sign readings from monitoring devices.",
    ),
    "patient_lab_results": FeatureGroup(
        name="patient_lab_results",
        entity="patient_id",
        features=[
            "patient_lab_results:blood_glucose",
            "patient_lab_results:cholesterol_total",
            "patient_lab_results:cholesterol_hdl",
            "patient_lab_results:cholesterol_ldl",
            "patient_lab_results:creatinine",
            "patient_lab_results:hemoglobin",
        ],
        description="Most recent lab test results.",
    ),
    "patient_risk_scores": FeatureGroup(
        name="patient_risk_scores",
        entity="patient_id",
        features=[
            "patient_risk_scores:diabetes_risk",
            "patient_risk_scores:heart_disease_risk",
            "patient_risk_scores:liver_disease_risk",
            "patient_risk_scores:kidney_disease_risk",
            "patient_risk_scores:readmission_risk",
        ],
        description="Pre-computed ML risk scores per disease.",
    ),
}


# ── Client ───────────────────────────────────────────────────────────


class FeatureStoreClient:
    """Thread-safe singleton Feast client with graceful degradation.

    When ``FEAST_REPO_PATH`` is not set or the Feast repo fails to
    initialise the client returns ``None`` for every query and logs a
    warning once at startup.
    """

    _instance: Optional[FeatureStoreClient] = None
    _lock = threading.Lock()

    def __new__(cls) -> FeatureStoreClient:
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._init_client()
                cls._instance = inst
            return cls._instance

    # ── Initialisation ───────────────────────────────────────────

    def _init_client(self) -> None:
        self._op_lock = threading.Lock()
        self._store: Any = None
        self._available: bool = False

        if not FEAST_REPO_PATH:
            logger.info(
                "FEAST_REPO_PATH not set — feature store client disabled."
            )
            return

        if not os.path.isdir(FEAST_REPO_PATH):
            logger.warning(
                "FEAST_REPO_PATH=%s does not exist — feature store disabled.",
                FEAST_REPO_PATH,
            )
            return

        try:
            from feast import FeatureStore  # type: ignore[import-untyped]

            self._store = FeatureStore(repo_path=FEAST_REPO_PATH)
            self._available = True
            logger.info(
                "Feast feature store initialised from %s", FEAST_REPO_PATH
            )
        except Exception as exc:
            logger.warning(
                "Failed to initialise Feast feature store (disabled): %s", exc
            )

    @property
    def is_available(self) -> bool:
        """Return ``True`` when Feast is connected."""
        return self._available

    # ── Online Features ──────────────────────────────────────────

    def get_online_features(
        self,
        entity_ids: List[Dict[str, Any]],
        feature_refs: List[str],
    ) -> Optional[Dict[str, List[Any]]]:
        """Retrieve real-time feature values from the online store.

        Parameters
        ----------
        entity_ids:
            List of entity key dicts, e.g.
            ``[{"patient_id": 1}, {"patient_id": 2}]``.
        feature_refs:
            Feature references in ``"feature_view:feature"`` format.

        Returns
        -------
        dict | None
            ``{feature_name: [values]}`` or ``None`` if unavailable.
        """
        with self._op_lock:
            if not self._available:
                logger.warning(
                    "Feast unavailable — cannot serve online features."
                )
                return None

            try:
                result = self._store.get_online_features(
                    features=feature_refs,
                    entity_rows=entity_ids,
                )
                feature_dict: Dict[str, List[Any]] = result.to_dict()
                logger.debug(
                    "Retrieved %d online features for %d entities",
                    len(feature_refs),
                    len(entity_ids),
                )
                return feature_dict
            except Exception as exc:
                logger.error("Online feature retrieval failed: %s", exc)
                return None

    # ── Historical Features ──────────────────────────────────────

    def get_historical_features(
        self,
        entity_df: Any,
        feature_refs: List[str],
    ) -> Optional[Any]:
        """Create a point-in-time correct training dataset.

        Parameters
        ----------
        entity_df:
            Pandas ``DataFrame`` with entity keys and an
            ``event_timestamp`` column.
        feature_refs:
            Feature references to join.

        Returns
        -------
        DataFrame | None
            Joined training ``DataFrame`` or ``None``.
        """
        with self._op_lock:
            if not self._available:
                logger.warning(
                    "Feast unavailable — cannot retrieve historical features."
                )
                return None

            try:
                retrieval_job = self._store.get_historical_features(
                    entity_df=entity_df,
                    features=feature_refs,
                )
                df = retrieval_job.to_df()
                logger.info(
                    "Retrieved historical features: %d rows × %d cols",
                    len(df),
                    len(df.columns),
                )
                return df
            except Exception as exc:
                logger.error("Historical feature retrieval failed: %s", exc)
                return None

    # ── Materialisation ──────────────────────────────────────────

    def materialize(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> bool:
        """Trigger feature materialisation from offline to online store.

        Parameters
        ----------
        start_date:
            Inclusive start of the materialisation window.
        end_date:
            Inclusive end of the materialisation window.

        Returns
        -------
        bool
            ``True`` on success, ``False`` otherwise.
        """
        with self._op_lock:
            if not self._available:
                logger.warning(
                    "Feast unavailable — cannot run materialisation."
                )
                return False

            try:
                self._store.materialize(
                    start_date=start_date,
                    end_date=end_date,
                )
                logger.info(
                    "Materialisation complete: %s → %s",
                    start_date.isoformat(),
                    end_date.isoformat(),
                )
                return True
            except Exception as exc:
                logger.error("Materialisation failed: %s", exc)
                return False

    # ── Convenience Helpers ──────────────────────────────────────

    def get_feature_group(self, group_name: str) -> Optional[FeatureGroup]:
        """Look up a predefined feature group by name."""
        return FEATURE_GROUPS.get(group_name)

    def list_feature_groups(self) -> List[str]:
        """Return the names of all predefined feature groups."""
        return list(FEATURE_GROUPS.keys())

    def get_patient_features(
        self,
        patient_ids: List[int],
        group_name: str,
    ) -> Optional[Dict[str, List[Any]]]:
        """Convenience method: get online features for patients by group.

        Parameters
        ----------
        patient_ids:
            List of patient integer IDs.
        group_name:
            One of the predefined feature group names.

        Returns
        -------
        dict | None
            Feature dict or ``None``.
        """
        group = self.get_feature_group(group_name)
        if group is None:
            logger.warning("Unknown feature group: %s", group_name)
            return None

        entity_ids = [{group.entity: pid} for pid in patient_ids]
        return self.get_online_features(entity_ids, group.features)


# ── Module-level singleton ───────────────────────────────────────────

feature_store_client = FeatureStoreClient()
