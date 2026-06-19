"""
Experiment Tracker — MLflow Training & Inference Metrics
========================================================
Thread-safe singleton wrapper around MLflow for logging training runs,
inference metrics, and model registry operations.

Falls back silently to local-only logging when the MLflow tracking server
is unreachable, following the same graceful-degradation pattern used by
:pymod:`backend.cache_service`.

Usage::

    from backend.experiment_tracker import experiment_tracker

    experiment_tracker.log_training_run(
        model_name="diabetes",
        params={"n_estimators": 200},
        metrics={"accuracy": 0.93, "f1": 0.91, "auc": 0.95},
        artifacts_path="backend/diabetes_model.pkl",
    )
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MLFLOW_TRACKING_URI = os.environ.get(
    "MLFLOW_TRACKING_URI", "http://127.0.0.1:5000"
)


# ── Data Structures ──────────────────────────────────────────────────


@dataclass
class TrainingRunRecord:
    """In-memory record kept when MLflow is unavailable."""

    model_name: str
    params: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    artifacts_path: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class PredictionMetricRecord:
    """Lightweight inference telemetry point."""

    model_name: str
    latency_ms: float
    confidence: float
    prediction_class: str
    timestamp: float = field(default_factory=time.time)


# ── Tracker ──────────────────────────────────────────────────────────


class ExperimentTracker:
    """Thread-safe singleton MLflow wrapper with graceful degradation.

    When the MLflow tracking server is unreachable the tracker logs a
    single warning at startup and silently stores records in memory so
    the rest of the application is never blocked.
    """

    _instance: Optional[ExperimentTracker] = None
    _lock = threading.Lock()

    def __new__(cls) -> ExperimentTracker:
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._init_tracker()
                cls._instance = inst
            return cls._instance

    # ── Initialisation ───────────────────────────────────────────

    def _init_tracker(self) -> None:
        self._op_lock = threading.Lock()
        self._mlflow: Any = None
        self._mlflow_client: Any = None
        self._available: bool = False
        # Fallback stores when MLflow is offline
        self._local_training_runs: List[TrainingRunRecord] = []
        self._local_prediction_metrics: List[PredictionMetricRecord] = []

        try:
            import mlflow  # type: ignore[import-untyped]
            import mlflow.tracking  # type: ignore[import-untyped]

            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            # Lightweight connectivity test
            client = mlflow.tracking.MlflowClient()
            client.search_experiments(max_results=1)

            self._mlflow = mlflow
            self._mlflow_client = client
            self._available = True
            logger.info(
                "Connected to MLflow tracking server at %s",
                MLFLOW_TRACKING_URI,
            )
        except Exception as exc:
            logger.warning(
                "MLflow tracking unavailable (falling back to in-memory): %s",
                exc,
            )

    @property
    def is_available(self) -> bool:
        """Return ``True`` when the MLflow backend is reachable."""
        return self._available

    # ── Training Run Logging ─────────────────────────────────────

    def log_training_run(
        self,
        model_name: str,
        params: Dict[str, Any],
        metrics: Dict[str, float],
        artifacts_path: Optional[str] = None,
    ) -> Optional[str]:
        """Log a training run with hyperparameters, metrics, and artifacts.

        Parameters
        ----------
        model_name:
            Logical model identifier (e.g. ``"diabetes"``).
        params:
            Hyperparameter dict.
        metrics:
            Must include standard keys: ``accuracy``, ``f1``, ``auc``.
        artifacts_path:
            Optional local path to model artifact directory or file.

        Returns
        -------
        str | None
            The MLflow ``run_id`` on success, or ``None`` if MLflow is
            unavailable.
        """
        with self._op_lock:
            if not self._available:
                self._local_training_runs.append(
                    TrainingRunRecord(
                        model_name=model_name,
                        params=params,
                        metrics=metrics,
                        artifacts_path=artifacts_path,
                    )
                )
                logger.debug(
                    "Stored training run locally for model=%s", model_name
                )
                return None

            try:
                mlflow = self._mlflow
                experiment_name = f"healthcare_{model_name}"
                mlflow.set_experiment(experiment_name)

                with mlflow.start_run(run_name=f"{model_name}_training") as run:
                    mlflow.log_params(params)
                    mlflow.log_metrics(metrics)
                    if artifacts_path and os.path.exists(artifacts_path):
                        mlflow.log_artifacts(artifacts_path)
                    mlflow.set_tag("model_name", model_name)
                    mlflow.set_tag("stage", "training")

                    run_id: str = run.info.run_id
                    logger.info(
                        "Logged training run for model=%s run_id=%s",
                        model_name,
                        run_id,
                    )
                    return run_id
            except Exception as exc:
                logger.error("Failed to log training run: %s", exc)
                self._local_training_runs.append(
                    TrainingRunRecord(
                        model_name=model_name,
                        params=params,
                        metrics=metrics,
                        artifacts_path=artifacts_path,
                    )
                )
                return None

    # ── Prediction / Inference Metrics ───────────────────────────

    def log_prediction_metrics(
        self,
        model_name: str,
        latency_ms: float,
        confidence: float,
        prediction_class: str,
    ) -> None:
        """Log a single inference telemetry data-point.

        Parameters
        ----------
        model_name:
            Model that served the prediction.
        latency_ms:
            End-to-end inference latency in milliseconds.
        confidence:
            Model confidence score (0-1).
        prediction_class:
            Predicted class label (e.g. ``"High Risk"``).
        """
        with self._op_lock:
            if not self._available:
                self._local_prediction_metrics.append(
                    PredictionMetricRecord(
                        model_name=model_name,
                        latency_ms=latency_ms,
                        confidence=confidence,
                        prediction_class=prediction_class,
                    )
                )
                return

            try:
                mlflow = self._mlflow
                experiment_name = f"healthcare_{model_name}_inference"
                mlflow.set_experiment(experiment_name)

                with mlflow.start_run(
                    run_name=f"{model_name}_prediction"
                ):
                    mlflow.log_metrics(
                        {
                            "latency_ms": latency_ms,
                            "confidence": confidence,
                        }
                    )
                    mlflow.set_tag("model_name", model_name)
                    mlflow.set_tag("prediction_class", prediction_class)
                    mlflow.set_tag("stage", "inference")
            except Exception as exc:
                logger.error("Failed to log prediction metrics: %s", exc)
                self._local_prediction_metrics.append(
                    PredictionMetricRecord(
                        model_name=model_name,
                        latency_ms=latency_ms,
                        confidence=confidence,
                        prediction_class=prediction_class,
                    )
                )

    # ── Model Registry Queries ───────────────────────────────────

    def get_best_model(
        self,
        experiment_name: str,
        metric: str = "accuracy",
    ) -> Optional[Dict[str, Any]]:
        """Return the best run for *experiment_name* ranked by *metric*.

        Returns
        -------
        dict | None
            ``{"run_id", "params", "metrics"}`` or ``None``.
        """
        with self._op_lock:
            if not self._available:
                logger.warning(
                    "MLflow unavailable — cannot query best model for %s",
                    experiment_name,
                )
                return None

            try:
                client = self._mlflow_client
                experiment = client.get_experiment_by_name(experiment_name)
                if experiment is None:
                    logger.warning(
                        "Experiment '%s' not found in MLflow",
                        experiment_name,
                    )
                    return None

                runs = client.search_runs(
                    experiment_ids=[experiment.experiment_id],
                    order_by=[f"metrics.{metric} DESC"],
                    max_results=1,
                )
                if not runs:
                    return None

                best = runs[0]
                return {
                    "run_id": best.info.run_id,
                    "params": dict(best.data.params),
                    "metrics": dict(best.data.metrics),
                }
            except Exception as exc:
                logger.error("Failed to query best model: %s", exc)
                return None

    def register_model(
        self,
        run_id: str,
        model_name: str,
        stage: str = "Staging",
    ) -> Optional[str]:
        """Promote a run's model artifact into the MLflow Model Registry.

        Parameters
        ----------
        run_id:
            MLflow run containing the logged model artifact.
        model_name:
            Registry name for the model.
        stage:
            Target stage — ``"Staging"`` or ``"Production"``.

        Returns
        -------
        str | None
            The model version string, or ``None`` on failure.
        """
        with self._op_lock:
            if not self._available:
                logger.warning(
                    "MLflow unavailable — cannot register model %s",
                    model_name,
                )
                return None

            try:
                mlflow = self._mlflow
                model_uri = f"runs:/{run_id}/model"
                result = mlflow.register_model(model_uri, model_name)

                client = self._mlflow_client
                client.transition_model_version_stage(
                    name=model_name,
                    version=result.version,
                    stage=stage,
                )
                logger.info(
                    "Registered model=%s version=%s stage=%s",
                    model_name,
                    result.version,
                    stage,
                )
                return str(result.version)
            except Exception as exc:
                logger.error("Failed to register model: %s", exc)
                return None

    # ── Diagnostics ──────────────────────────────────────────────

    def flush_local_records(self) -> Dict[str, int]:
        """Return and clear locally buffered records (useful for diagnostics).

        Returns
        -------
        dict
            Counts of flushed training runs and prediction metrics.
        """
        with self._op_lock:
            training_count = len(self._local_training_runs)
            prediction_count = len(self._local_prediction_metrics)
            self._local_training_runs.clear()
            self._local_prediction_metrics.clear()
            return {
                "training_runs_flushed": training_count,
                "prediction_metrics_flushed": prediction_count,
            }


# ── Module-level singleton ───────────────────────────────────────────

experiment_tracker = ExperimentTracker()
